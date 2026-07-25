"""Behavioral tests for create-only spec task registration."""

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from agentic import bd, register  # noqa: E402
from agentic.lock import LockTimeout, RepoLock  # noqa: E402

requires_bd = pytest.mark.skipif(
    bd.bd_which() is None, reason="bd not installed on PATH"
)


def _git_store(tmp_path):
    store = tmp_path / "store"
    store.mkdir()
    subprocess.run(["git", "init", "-q", "."], cwd=store, check=True)
    subprocess.run(["git", "config", "user.email", "t@e.com"], cwd=store, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=store, check=True)
    bd.bd_init(str(store))
    return store


def _write_task(store, name, body):
    tasks = store / "specs" / "demo" / "tasks"
    tasks.mkdir(parents=True, exist_ok=True)
    path = tasks / name
    path.write_text(body, encoding="utf-8")
    return path


def _issues(store):
    rows = [
        json.loads(line)
        for line in (bd.bd_export(cwd=str(store)) or "").splitlines()
        if line.strip()
    ]
    return {row["external_ref"]: row for row in rows if row.get("external_ref")}


def _metadata(issue):
    value = issue.get("metadata") or {}
    return json.loads(value) if isinstance(value, str) else value


def _agentic(store, *args):
    env = {**os.environ, "PYTHONPATH": str(REPO_ROOT)}
    return subprocess.run(
        [sys.executable, "-m", "agentic", *args],
        cwd=store,
        env=env,
        capture_output=True,
        text=True,
    )


TASK_ONE = """\
# Task 01: establish the base

Status: pending
Depends on: none
Budget: 12 turns
Rigor: prototype
Touch: tests/a.py, src/a.py

## Goal

Create the base behavior.

## Steps

1. Implement it.
"""

TASK_TWO = """\
# Task 02: build on the base

Status: blocked
Depends on: 01
Budget: 8 turns
Touch: src/b.py

## Goal

Build the dependent behavior.
"""


def test_definition_hash_is_canonical_and_ignores_status(tmp_path):
    store = tmp_path / "repo"
    path = _write_task(store, "01-base.md", TASK_ONE)
    first = register.parse_task(path, store)
    path.write_text(
        TASK_ONE.replace("Status: pending", "Status: done").replace(
            "tests/a.py, src/a.py", "src/a.py, tests/a.py"
        ),
        encoding="utf-8",
    )
    second = register.parse_task(path, store)

    canonical = {
        "budget": "12 turns",
        "goal": "Create the base behavior.",
        "path": "specs/demo/tasks/01-base.md",
        "prerequisites": [],
        "rigor": "prototype",
        "schema_version": 1,
        "title": "Task 01: establish the base",
        "touch": ["src/a.py", "tests/a.py"],
    }
    expected = hashlib.sha256(
        json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    assert register.definition_hash(first) == expected
    assert register.definition_hash(second) == expected


@requires_bd
def test_register_spec_runs_two_phase_happy_path_with_exact_edge_direction(tmp_path):
    store = _git_store(tmp_path)
    _write_task(store, "01-base.md", TASK_ONE)
    _write_task(store, "02-dependent.md", TASK_TWO)

    assert register.register_spec(store / "specs" / "demo", store_cwd=store) == 2
    issues = _issues(store)
    base = issues["spec-task:specs/demo/tasks/01-base.md"]
    dependent = issues["spec-task:specs/demo/tasks/02-dependent.md"]

    assert base["title"] == "Task 01: establish the base"
    assert base["description"] == "Create the base behavior."
    assert base["status"] == "open"
    assert _metadata(base) == {
        "budget": "12 turns",
        "definition_hash": register.definition_hash(
            register.parse_task(
                store / "specs/demo/tasks/01-base.md",
                store,
            )
        ),
        "registration_state": "complete",
        "rigor": "prototype",
        "source": "specs/demo/tasks/01-base.md",
        "touch": ["src/a.py", "tests/a.py"],
    }
    assert _metadata(dependent)["registration_state"] == "complete"
    assert {
        (edge["issue_id"], edge["depends_on_id"], edge["type"])
        for edge in dependent.get("dependencies", [])
    } == {(dependent["id"], base["id"], "blocks")}


@requires_bd
def test_cli_register_spec_dispatches_the_real_registrar(tmp_path):
    store = _git_store(tmp_path)
    _write_task(store, "01-base.md", TASK_ONE)

    result = _agentic(store, "register-spec", "specs/demo")
    assert result.returncode == 0, result.stderr
    assert result.stdout == "register-spec: 1 task(s) registered\n"
    assert "spec-task:specs/demo/tasks/01-base.md" in _issues(store)


@requires_bd
def test_interrupted_phase_two_recovers_and_same_hash_rerun_is_idempotent(
    tmp_path, monkeypatch
):
    store = _git_store(tmp_path)
    _write_task(store, "01-base.md", TASK_ONE)
    _write_task(store, "02-dependent.md", TASK_TWO)
    real_add = register._add_edge

    def interrupt(*_args, **_kwargs):
        raise RuntimeError("simulated phase-two interruption")

    monkeypatch.setattr(register, "_add_edge", interrupt)
    with pytest.raises(RuntimeError, match="interruption"):
        register.register_spec(store / "specs" / "demo", store_cwd=store)
    assert {
        _metadata(issue)["registration_state"] for issue in _issues(store).values()
    } == {"pending"}

    monkeypatch.setattr(register, "_add_edge", real_add)
    register.register_spec(store / "specs" / "demo", store_cwd=store)
    recovered = bd.bd_export(cwd=str(store))
    register.register_spec(store / "specs" / "demo", store_cwd=store)
    assert bd.bd_export(cwd=str(store)) == recovered


@requires_bd
def test_conflicting_definition_hash_fails_without_mutating_existing_issue(tmp_path):
    store = _git_store(tmp_path)
    path = _write_task(store, "01-base.md", TASK_ONE)
    register.register_spec(store / "specs" / "demo", store_cwd=store)
    before = bd.bd_export(cwd=str(store))

    path.write_text(
        TASK_ONE.replace("Create the base behavior.", "Change the definition."),
        encoding="utf-8",
    )
    with pytest.raises(register.RegistrationConflict, match="definition hash"):
        register.register_spec(store / "specs" / "demo", store_cwd=store)
    assert bd.bd_export(cwd=str(store)) == before


@requires_bd
def test_conflicting_existing_edge_fails_without_replacing_it(tmp_path, monkeypatch):
    store = _git_store(tmp_path)
    _write_task(store, "01-base.md", TASK_ONE)
    _write_task(store, "02-dependent.md", TASK_TWO)

    monkeypatch.setattr(
        register,
        "_add_edge",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("stop")),
    )
    with pytest.raises(RuntimeError, match="stop"):
        register.register_spec(store / "specs" / "demo", store_cwd=store)
    issues = _issues(store)
    base = issues["spec-task:specs/demo/tasks/01-base.md"]
    dependent = issues["spec-task:specs/demo/tasks/02-dependent.md"]
    bd._run(
        ["dep", "add", dependent["id"], base["id"], "--type", "related"],
        cwd=str(store),
    )

    with pytest.raises(register.RegistrationConflict, match="conflicting edge"):
        register.register_spec(store / "specs" / "demo", store_cwd=store)
    edge = _issues(store)["spec-task:specs/demo/tasks/02-dependent.md"][
        "dependencies"
    ][0]
    assert edge["type"] == "related"


@requires_bd
def test_rerun_only_changes_registrar_owned_registration_state(tmp_path):
    store = _git_store(tmp_path)
    _write_task(store, "01-base.md", TASK_ONE)
    register.register_spec(store / "specs" / "demo", store_cwd=store)
    issue = _issues(store)["spec-task:specs/demo/tasks/01-base.md"]
    metadata = {**_metadata(issue), "registration_state": "pending", "owner_data": 7}
    bd._run(
        [
            "update",
            issue["id"],
            "--status",
            "blocked",
            "--priority",
            "0",
            "--assignee",
            "somebody",
            "--metadata",
            json.dumps(metadata),
        ],
        cwd=str(store),
    )
    bd._run(["comment", issue["id"], "keep me"], cwd=str(store))

    register.register_spec(store / "specs" / "demo", store_cwd=store)
    after = _issues(store)["spec-task:specs/demo/tasks/01-base.md"]
    assert after["status"] == "blocked"
    assert after["priority"] == 0
    assert after["assignee"] == "somebody"
    assert after["comment_count"] == 1
    assert _metadata(after)["owner_data"] == 7
    assert _metadata(after)["registration_state"] == "complete"


@requires_bd
def test_register_spec_takes_the_existing_repo_lock(tmp_path):
    store = _git_store(tmp_path)
    _write_task(store, "01-base.md", TASK_ONE)
    with RepoLock(str(store)):
        with pytest.raises(LockTimeout):
            register.register_spec(
                store / "specs" / "demo",
                store_cwd=store,
                acquire_timeout=0.2,
            )
