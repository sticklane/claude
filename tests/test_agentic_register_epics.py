"""Behavioral tests for the epic bead a feature spec registers (agentic-3syx).

A feature's tasks group under one epic so /drain works the highest-priority
feature to completion instead of an aimless queue. These live apart from
tests/test_agentic_register.py because that file's surface-inventory
classification is pinned by a committed fragment, and a fragment can only be
superseded by the baseline — new coverage arrives as a new surface.
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from agentic import bd, register  # noqa: E402

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


def _write_spec(store, body):
    spec_dir = store / "specs" / "demo"
    spec_dir.mkdir(parents=True, exist_ok=True)
    path = spec_dir / "SPEC.md"
    path.write_text(body, encoding="utf-8")
    return path


def _issues(store):
    rows = [
        json.loads(line)
        for line in (bd.bd_export(cwd=str(store)) or "").splitlines()
        if line.strip()
    ]
    return {row["external_ref"]: row for row in rows if row.get("external_ref")}


TASK_ONE = """\
# Task 01: establish the base

Status: pending
Depends on: none
Budget: 12 turns
Touch: src/a.py

## Goal

Create the base behavior.
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

SPEC_FEATURE = """\
# Notes sync

Priority: P0

## Goal

Keep notes in sync across devices.
"""

SPEC_JANITORIAL = """\
# Tidy the worktrees

Kind: janitorial

## Goal

Clear stale checkouts.
"""


def _parent_edges(issue):
    return [
        e for e in issue.get("dependencies", []) or [] if e["type"] == "parent-child"
    ]


def test_parse_spec_defaults_to_a_p2_feature(tmp_path):
    store = tmp_path / "repo"
    _write_spec(store, "# Bare spec\n\n## Goal\n\nDo the thing.\n")
    spec = register.parse_spec(store / "specs" / "demo", store)

    assert spec["title"] == "Bare spec"
    assert spec["priority"] == "2"
    assert spec["goal"] == "Do the thing."


def test_parse_spec_returns_none_for_janitorial_work(tmp_path):
    store = tmp_path / "repo"
    _write_spec(store, SPEC_JANITORIAL)
    assert register.parse_spec(store / "specs" / "demo", store) is None


def test_parse_spec_returns_none_when_the_spec_file_is_absent(tmp_path):
    store = tmp_path / "repo"
    (store / "specs" / "demo").mkdir(parents=True)
    assert register.parse_spec(store / "specs" / "demo", store) is None


@requires_bd
def test_register_spec_creates_an_epic_and_parents_every_task_to_it(tmp_path):
    store = _git_store(tmp_path)
    _write_spec(store, SPEC_FEATURE)
    _write_task(store, "01-base.md", TASK_ONE)
    _write_task(store, "02-dependent.md", TASK_TWO)

    register.register_spec(store / "specs" / "demo", store_cwd=store)
    issues = _issues(store)
    epic = issues["spec:specs/demo/SPEC.md"]

    assert epic["title"] == "Notes sync"
    assert epic["issue_type"] == "epic"
    assert epic["priority"] == 0
    assert epic["description"] == "Keep notes in sync across devices."

    for ref in (
        "spec-task:specs/demo/tasks/01-base.md",
        "spec-task:specs/demo/tasks/02-dependent.md",
    ):
        edges = {
            (e["issue_id"], e["depends_on_id"], e["type"])
            for e in issues[ref].get("dependencies", [])
        }
        assert (issues[ref]["id"], epic["id"], "parent-child") in edges


@requires_bd
def test_register_spec_keeps_prerequisite_edges_alongside_the_epic(tmp_path):
    """The epic edge is additive: task ordering within the feature survives."""
    store = _git_store(tmp_path)
    _write_spec(store, SPEC_FEATURE)
    _write_task(store, "01-base.md", TASK_ONE)
    _write_task(store, "02-dependent.md", TASK_TWO)

    register.register_spec(store / "specs" / "demo", store_cwd=store)
    issues = _issues(store)
    base = issues["spec-task:specs/demo/tasks/01-base.md"]
    dependent = issues["spec-task:specs/demo/tasks/02-dependent.md"]

    assert (dependent["id"], base["id"], "blocks") in {
        (e["issue_id"], e["depends_on_id"], e["type"])
        for e in dependent.get("dependencies", [])
    }


@requires_bd
def test_register_spec_writes_no_epic_for_janitorial_work(tmp_path):
    store = _git_store(tmp_path)
    _write_spec(store, SPEC_JANITORIAL)
    _write_task(store, "01-base.md", TASK_ONE)

    register.register_spec(store / "specs" / "demo", store_cwd=store)
    issues = _issues(store)

    assert "spec:specs/demo/SPEC.md" not in issues
    assert not _parent_edges(issues["spec-task:specs/demo/tasks/01-base.md"])


@requires_bd
def test_register_spec_without_a_spec_file_registers_tasks_unparented(tmp_path):
    store = _git_store(tmp_path)
    _write_task(store, "01-base.md", TASK_ONE)

    assert register.register_spec(store / "specs" / "demo", store_cwd=store) == 1
    assert "spec:specs/demo/SPEC.md" not in _issues(store)


@requires_bd
def test_reregistering_reuses_the_existing_epic(tmp_path):
    """Registration is create-only: a second run adds no second epic or edge."""
    store = _git_store(tmp_path)
    _write_spec(store, SPEC_FEATURE)
    _write_task(store, "01-base.md", TASK_ONE)

    register.register_spec(store / "specs" / "demo", store_cwd=store)
    first = _issues(store)["spec:specs/demo/SPEC.md"]["id"]
    register.register_spec(store / "specs" / "demo", store_cwd=store)
    issues = _issues(store)

    assert issues["spec:specs/demo/SPEC.md"]["id"] == first
    assert len([r for r in issues.values() if r.get("issue_type") == "epic"]) == 1
    assert len(_parent_edges(issues["spec-task:specs/demo/tasks/01-base.md"])) == 1
