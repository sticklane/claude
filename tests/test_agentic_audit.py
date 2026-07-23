"""SPEC S14 / Migration step 7: ``agentic audit [--since DATE] [--dry-run]``
reads Claude Code session transcripts and the bd tracker, measures four
tool-adoption regression classes — structure lookups that bypassed
``agentic ctx`` for grep, dispatches that bypassed compose, verdict-schema
failures, and spend over cap — and files each NON-ZERO class as one tracker
task linked ``discovered-from`` a standing audit anchor issue. ``--dry-run``
prints the measures and writes nothing. A second run files nothing new
(dedup against open audit tasks).

The pure-measurement tests run without bd (they exercise the transcript
reader and detectors directly). The filing/dedup tests seed a real bd store
and drive the real ``agentic audit`` command through a subprocess, so they
exercise bd's actual create/dependency behaviour rather than a mock.
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

from agentic import audit  # noqa: E402
from agentic import bd  # noqa: E402

requires_bd = pytest.mark.skipif(
    bd.bd_which() is None, reason="bd not installed on PATH"
)


# --- transcript fixtures ----------------------------------------------------


def _assistant(tool_use, ts="2026-07-15T10:00:00Z"):
    return {
        "type": "assistant",
        "timestamp": ts,
        "message": {"content": [tool_use]},
    }


def _tool_use(name, **inp):
    return {"type": "tool_use", "name": name, "input": inp}


def _grep_bypass_record(ts="2026-07-15T10:00:00Z"):
    # A raw Grep for a symbol — a structure lookup that bypassed `agentic ctx`.
    return _assistant(_tool_use("Grep", pattern="def compute_frontier"), ts=ts)


def _compose_bypass_record(ts="2026-07-15T11:00:00Z"):
    # A Task dispatch whose prompt never went through `agentic compose`.
    return _assistant(
        _tool_use(
            "Task",
            subagent_type="general-purpose",
            prompt="Go implement the widget and report back.",
        ),
        ts=ts,
    )


def _write_transcripts(dir_path, records_by_file):
    dir_path.mkdir(parents=True, exist_ok=True)
    for name, records in records_by_file.items():
        (dir_path / name).write_text("\n".join(json.dumps(r) for r in records) + "\n")
    return dir_path


# --- pure measurement (no bd) ----------------------------------------------


def test_measure_counts_one_grep_and_one_compose_bypass(tmp_path):
    root = _write_transcripts(
        tmp_path / "projects",
        {
            "a.jsonl": [_grep_bypass_record()],
            "b.jsonl": [_compose_bypass_record()],
        },
    )
    counts = audit.measure(audit.discover_transcripts(root), cwd=str(tmp_path))
    assert counts["grep-bypass"] == 1
    assert counts["compose-bypass"] == 1
    assert counts["verdict-schema-failure"] == 0


def test_grep_led_bash_is_a_bypass_but_a_piped_grep_is_not():
    grep_led = _tool_use("Bash", command="grep -rn 'class Foo' agentic/")
    piped = _tool_use("Bash", command="git status --short | grep audit")
    assert audit.is_grep_bypass(grep_led)
    assert not audit.is_grep_bypass(piped)


def test_task_dispatch_through_compose_is_not_a_bypass():
    through = _tool_use(
        "Task",
        subagent_type="general-purpose",
        prompt="$(agentic compose bd-7)\nDo the task above.",
    )
    without = _tool_use("Task", subagent_type="general-purpose", prompt="just do it")
    assert not audit.is_compose_bypass(through)
    assert audit.is_compose_bypass(without)


def test_verdict_schema_failure_is_counted_from_tool_results(tmp_path):
    failure = {
        "type": "user",
        "timestamp": "2026-07-15T12:00:00Z",
        "message": {
            "content": [
                {
                    "type": "tool_result",
                    "content": "verdict file failed schema validation:\n  - 'summary' is required",
                }
            ]
        },
    }
    root = _write_transcripts(tmp_path / "projects", {"c.jsonl": [failure]})
    counts = audit.measure(audit.discover_transcripts(root), cwd=str(tmp_path))
    assert counts["verdict-schema-failure"] == 1


def test_since_filters_out_older_events(tmp_path):
    root = _write_transcripts(
        tmp_path / "projects",
        {
            "old.jsonl": [_grep_bypass_record(ts="2026-06-01T10:00:00Z")],
            "new.jsonl": [_grep_bypass_record(ts="2026-07-15T10:00:00Z")],
        },
    )
    counts = audit.measure(
        audit.discover_transcripts(root), since="2026-07-01", cwd=str(tmp_path)
    )
    assert counts["grep-bypass"] == 1


# --- filing / dedup against a real bd store --------------------------------


def _seed_store(tmp_path):
    store = tmp_path / "store"
    store.mkdir()
    subprocess.run(["git", "init", "-q", "."], cwd=store, check=True)
    subprocess.run(["git", "config", "user.email", "t@e.com"], cwd=store, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=store, check=True)
    bd.bd_init(str(store))
    # Seed one ordinary issue so the store is non-empty (mirrors real use).
    jsonl = store / "seed.jsonl"
    jsonl.write_text(
        json.dumps(
            {
                "id": "seed-1",
                "title": "unrelated task",
                "status": "open",
                "issue_type": "task",
                "priority": 2,
            }
        )
        + "\n"
    )
    bd.bd_import(str(jsonl), cwd=str(store))
    return store


def _agentic(store, transcript_root, *args):
    env = dict(os.environ)
    env["PYTHONPATH"] = str(REPO_ROOT)
    env["BD_ACTOR"] = "auditor"
    env["AGENTIC_TRANSCRIPT_ROOT"] = str(transcript_root)
    return subprocess.run(
        [sys.executable, "-m", "agentic", *args],
        cwd=str(store),
        env=env,
        capture_output=True,
        text=True,
    )


def _discovered_from_anchor(store):
    """Titles of every issue linked discovered-from the audit anchor."""
    export = bd.bd_export(cwd=str(store)) or ""
    anchor_ids = {
        json.loads(l)["id"]
        for l in export.splitlines()
        if l.strip() and json.loads(l).get("title") == audit.ANCHOR_TITLE
    }
    titles = []
    for line in export.splitlines():
        line = line.strip()
        if not line:
            continue
        obj = json.loads(line)
        for dep in obj.get("dependencies") or []:
            if dep.get("type") == "discovered-from" and (
                dep.get("depends_on_id") in anchor_ids
            ):
                titles.append(obj.get("title", ""))
    return titles


@requires_bd
def test_audit_files_exactly_two_typed_tasks_linked_discovered_from(tmp_path):
    tr = _write_transcripts(
        tmp_path / "projects",
        {
            "a.jsonl": [_grep_bypass_record()],
            "b.jsonl": [_compose_bypass_record()],
        },
    )
    store = _seed_store(tmp_path)
    r = _agentic(store, tr, "audit", "--since", "2026-07-01")
    assert r.returncode == 0, r.stderr

    filed = _discovered_from_anchor(store)
    assert sorted(filed) == sorted(
        [audit.title_for("grep-bypass"), audit.title_for("compose-bypass")]
    ), filed


@requires_bd
def test_second_run_files_nothing_new(tmp_path):
    tr = _write_transcripts(
        tmp_path / "projects",
        {
            "a.jsonl": [_grep_bypass_record()],
            "b.jsonl": [_compose_bypass_record()],
        },
    )
    store = _seed_store(tmp_path)
    assert _agentic(store, tr, "audit", "--since", "2026-07-01").returncode == 0
    first = _discovered_from_anchor(store)
    assert len(first) == 2

    assert _agentic(store, tr, "audit", "--since", "2026-07-01").returncode == 0
    second = _discovered_from_anchor(store)
    assert second == first, "a second audit run must not re-file open findings"


@requires_bd
def test_dry_run_prints_measures_and_files_nothing(tmp_path):
    tr = _write_transcripts(
        tmp_path / "projects",
        {
            "a.jsonl": [_grep_bypass_record()],
            "b.jsonl": [_compose_bypass_record()],
        },
    )
    store = _seed_store(tmp_path)
    r = _agentic(store, tr, "audit", "--since", "2026-07-01", "--dry-run")
    assert r.returncode == 0, r.stderr
    # Measures are reported...
    assert "grep-bypass" in r.stdout
    assert "compose-bypass" in r.stdout
    # ...but nothing is filed.
    assert _discovered_from_anchor(store) == []
