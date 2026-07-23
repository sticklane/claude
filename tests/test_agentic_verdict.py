"""SPEC S5 / D7: ``agentic verdict <id> --file <path>`` validates a worker's
JSON result against ``agentic/schema/verdict.json`` (DONE/BLOCKED/DEFERRED,
typed Unblock, Discovered list), updates the task in bd, and files discovered
work as new issues linked ``discovered-from`` their origin.

Fixtures seed a real bd store (``bd_init`` + ``bd_import``) and drive the real
``agentic verdict`` command through a subprocess, so the tests exercise bd's
actual status/metadata/dependency behavior rather than a mock. Schema-shape
tests validate directly against the shipped schema file — no bd required.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from agentic import bd  # noqa: E402
from agentic import verdict as verdict_mod  # noqa: E402

requires_bd = pytest.mark.skipif(
    bd.bd_which() is None, reason="bd not installed on PATH"
)

SCHEMA_PATH = REPO_ROOT / "agentic" / "schema" / "verdict.json"


# --- schema shape (no bd) --------------------------------------------------


def _valid(doc):
    """True iff ``doc`` validates against the shipped verdict schema."""
    return verdict_mod.validation_errors(doc) == []


def test_schema_file_is_valid_json_schema():
    schema = json.loads(SCHEMA_PATH.read_text())
    assert schema.get("type") == "object"
    assert set(schema["properties"]["status"]["enum"]) == {
        "DONE",
        "BLOCKED",
        "DEFERRED",
    }


def test_accepts_minimal_done_verdict():
    assert _valid({"status": "DONE", "summary": "did the thing"})


def test_rejects_unknown_status():
    assert not _valid({"status": "MAYBE", "summary": "x"})


def test_rejects_missing_summary():
    assert not _valid({"status": "DONE"})


def test_rejects_unknown_top_level_field():
    assert not _valid({"status": "DONE", "summary": "x", "bogus": 1})


def test_blocked_requires_typed_unblock():
    # BLOCKED without an unblock object is rejected...
    assert not _valid({"status": "BLOCKED", "summary": "stuck"})
    # ...and the unblock type must be one of the four typed kinds.
    assert not _valid(
        {
            "status": "BLOCKED",
            "summary": "stuck",
            "unblock": {"type": "frobnicate", "detail": "x"},
        }
    )
    assert _valid(
        {
            "status": "BLOCKED",
            "summary": "stuck",
            "unblock": {"type": "ask", "detail": "which region?"},
        }
    )


def test_deferred_requires_a_question():
    assert not _valid({"status": "DEFERRED", "summary": "later"})
    assert _valid(
        {
            "status": "DEFERRED",
            "summary": "later",
            "deferred_questions": ["what is the retention window?"],
        }
    )


def test_discovered_items_require_a_title():
    assert not _valid(
        {"status": "DONE", "summary": "x", "discovered": [{"description": "no title"}]}
    )
    assert _valid(
        {
            "status": "DONE",
            "summary": "x",
            "discovered": [{"title": "found a bug", "priority": 1}],
        }
    )


# --- command behaviour against a real bd store -----------------------------


def _issue(id_, title, status="open", priority=1, touch=None):
    return {
        "id": id_,
        "title": title,
        "status": status,
        "priority": priority,
        "issue_type": "task",
        "metadata": {"touch": list(touch or [])},
    }


def _seed(tmp_path, rows):
    store = tmp_path / "store"
    store.mkdir()
    subprocess.run(["git", "init", "-q", "."], cwd=store, check=True)
    subprocess.run(["git", "config", "user.email", "t@e.com"], cwd=store, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=store, check=True)
    bd.bd_init(str(store))
    jsonl = store / "seed.jsonl"
    jsonl.write_text("\n".join(json.dumps(r) for r in rows) + "\n")
    bd.bd_import(str(jsonl), cwd=str(store))
    return store


def _agentic(store, *args, actor="worker"):
    env = dict(os.environ)
    env["PYTHONPATH"] = str(REPO_ROOT)
    env["BD_ACTOR"] = actor
    return subprocess.run(
        [sys.executable, "-m", "agentic", *args],
        cwd=str(store),
        env=env,
        capture_output=True,
        text=True,
    )


def _status_of(store, id_):
    # Read via export, not `bd list` — list filters out closed issues.
    for line in (bd.bd_export(cwd=str(store)) or "").splitlines():
        line = line.strip()
        if not line:
            continue
        obj = json.loads(line)
        if obj.get("id") == id_:
            return obj.get("status")
    return None


def _metadata_of(store, id_):
    for line in (bd.bd_export(cwd=str(store)) or "").splitlines():
        line = line.strip()
        if not line:
            continue
        obj = json.loads(line)
        if obj.get("id") == id_:
            return obj.get("metadata") or {}
    return {}


def _write_verdict(store, doc):
    path = store / "verdict.json"
    path.write_text(json.dumps(doc))
    return path


@requires_bd
def test_done_verdict_closes_the_task(tmp_path):
    store = _seed(tmp_path, [_issue("vd-1", "do it")])
    vf = _write_verdict(store, {"status": "DONE", "summary": "done"})
    r = _agentic(store, "verdict", "vd-1", "--file", str(vf))
    assert r.returncode == 0, r.stderr
    assert _status_of(store, "vd-1") == "closed"


@requires_bd
def test_blocked_verdict_records_typed_unblock(tmp_path):
    store = _seed(tmp_path, [_issue("vd-2", "blocked one")])
    vf = _write_verdict(
        store,
        {
            "status": "BLOCKED",
            "summary": "cannot proceed",
            "unblock": {"type": "provision", "detail": "need an API key"},
        },
    )
    r = _agentic(store, "verdict", "vd-2", "--file", str(vf))
    assert r.returncode == 0, r.stderr
    assert _status_of(store, "vd-2") == "blocked"
    meta = _metadata_of(store, "vd-2")
    assert meta.get("unblock", {}).get("type") == "provision"


@requires_bd
def test_schema_invalid_file_fails_and_leaves_task_untouched(tmp_path):
    store = _seed(tmp_path, [_issue("vd-3", "keep open")])
    vf = _write_verdict(store, {"status": "BLOCKED", "summary": "no unblock given"})
    r = _agentic(store, "verdict", "vd-3", "--file", str(vf))
    assert r.returncode != 0
    assert _status_of(store, "vd-3") == "open"  # untouched by a rejected verdict


@requires_bd
def test_discovered_work_is_filed_with_a_discovered_from_edge(tmp_path):
    store = _seed(tmp_path, [_issue("vd-4", "origin task")])
    vf = _write_verdict(
        store,
        {
            "status": "DONE",
            "summary": "done, but found more",
            "discovered": [{"title": "follow-up cleanup", "priority": 2}],
        },
    )
    r = _agentic(store, "verdict", "vd-4", "--file", str(vf))
    assert r.returncode == 0, r.stderr

    # A new issue exists, linked discovered-from the origin.
    export = bd.bd_export(cwd=str(store)) or ""
    edge_found = False
    for line in export.splitlines():
        line = line.strip()
        if not line:
            continue
        obj = json.loads(line)
        for dep in obj.get("dependencies") or []:
            if (
                dep.get("type") == "discovered-from"
                and dep.get("depends_on_id") == "vd-4"
            ):
                edge_found = True
    assert edge_found, "no discovered-from edge back to the origin task"


@requires_bd
def test_reapplying_a_discovered_verdict_does_not_double_file(tmp_path):
    # The D9 push-rejection retry re-runs the semantic apply; discovered
    # filing must be idempotent so it never files the same follow-up twice.
    from agentic import verdict as vmod
    from agentic import sync as smod

    store = _seed(tmp_path, [_issue("vd-6", "origin")])
    doc = {
        "status": "DONE",
        "summary": "found one",
        "discovered": [{"title": "dup-guard follow-up"}],
    }
    smod.sync_write(str(store), lambda root: vmod._apply_verdict(root, "vd-6", doc))
    smod.sync_write(str(store), lambda root: vmod._apply_verdict(root, "vd-6", doc))

    export = bd.bd_export(cwd=str(store)) or ""
    filed = 0
    for line in export.splitlines():
        line = line.strip()
        if not line:
            continue
        obj = json.loads(line)
        for dep in obj.get("dependencies") or []:
            if (
                dep.get("type") == "discovered-from"
                and dep.get("depends_on_id") == "vd-6"
            ):
                filed += 1
    assert filed == 1, f"expected exactly one filed discovered item, got {filed}"


@requires_bd
def test_verdict_commits_the_exported_jsonl(tmp_path):
    store = _seed(tmp_path, [_issue("vd-5", "commit me")])
    vf = _write_verdict(store, {"status": "DONE", "summary": "done"})
    r = _agentic(store, "verdict", "vd-5", "--file", str(vf))
    assert r.returncode == 0, r.stderr
    # The committed JSONL reflects the close (D9: export+commit per command).
    committed = subprocess.run(
        ["git", "show", "HEAD:.beads/issues.jsonl"],
        cwd=str(store),
        capture_output=True,
        text=True,
    )
    assert committed.returncode == 0, "issues.jsonl was not committed"
    closed = [
        json.loads(l)
        for l in committed.stdout.splitlines()
        if l.strip() and json.loads(l).get("id") == "vd-5"
    ]
    assert closed and closed[0]["status"] == "closed"
