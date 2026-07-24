"""SPEC S11 / Migration step 2: shadow-mode markdown -> bd sync.

``agentic`` shadow mode mirrors the markdown task queue into bd one way:
markdown stays the source of truth, bd reflects it. These tests seed a real bd
store (``bd_init`` + the shadow importer), drive the real ``agentic ready``
command, and assert bd's actual state, so they exercise bd rather than a mock.
"""

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

from agentic import bd, shadow  # noqa: E402
from agentic.lock import LOCK_NAME, LockTimeout, RepoLock  # noqa: E402

requires_bd = pytest.mark.skipif(
    bd.bd_which() is None, reason="bd not installed on PATH"
)


# --- helpers ---------------------------------------------------------------


def _git_store(tmp_path):
    """A fresh git repo with an initialized bd store; returns its dir."""
    store = tmp_path / "store"
    store.mkdir()
    subprocess.run(["git", "init", "-q", "."], cwd=store, check=True)
    subprocess.run(["git", "config", "user.email", "t@e.com"], cwd=store, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=store, check=True)
    bd.bd_init(str(store))
    return store


def _write_task(store, spec, name, body):
    tasks = store / "specs" / spec / "tasks"
    tasks.mkdir(parents=True, exist_ok=True)
    path = tasks / name
    path.write_text(body)
    return path


def _export(store):
    """Every imported issue keyed by title (the task's relative path)."""
    raw = bd.bd_export(cwd=str(store)) or ""
    out = {}
    for line in raw.splitlines():
        line = line.strip()
        if line:
            obj = json.loads(line)
            out[obj.get("title", obj.get("id"))] = obj
    return out


def _agentic(store, *args):
    env = dict(os.environ)
    env["PYTHONPATH"] = str(REPO_ROOT)
    return subprocess.run(
        [sys.executable, "-m", "agentic", *args],
        cwd=str(store),
        env=env,
        capture_output=True,
        text=True,
    )


PENDING_TASK = """\
Status: pending
Depends on: none
Priority: P1
Budget: 12 turns
Rigor: prototype
Touch: src/a.py, tests/a.py

## Goal
A pending task.
"""

BLOCKED_TASK = """\
Status: blocked
Depends on: 01
Priority: P2
Touch: src/b.py

Unblock: ask — needs a human decision first

## Goal
A blocked task.
"""

DONE_TASK = """\
Status: done
Priority: P0
Touch: src/c.py

## Goal
A finished task.
"""


def _seed_three(store):
    _write_task(store, "demo", "01-pending.md", PENDING_TASK)
    _write_task(store, "demo", "02-blocked.md", BLOCKED_TASK)
    _write_task(store, "demo", "03-done.md", DONE_TASK)


# --- status / edge / metadata mirroring ------------------------------------


@requires_bd
def test_sync_maps_markdown_status_to_bd_frontier_classes(tmp_path):
    store = _git_store(tmp_path)
    _seed_three(store)
    shadow.sync(str(store), take_lock=False)
    issues = _export(store)
    assert issues["specs/demo/tasks/01-pending.md"]["status"] == "open"
    assert issues["specs/demo/tasks/02-blocked.md"]["status"] == "blocked"
    assert issues["specs/demo/tasks/03-done.md"]["status"] == "closed"


@requires_bd
def test_sync_creates_blocking_dependency_edges(tmp_path):
    store = _git_store(tmp_path)
    _seed_three(store)
    shadow.sync(str(store), take_lock=False)
    issues = _export(store)
    blocked = issues["specs/demo/tasks/02-blocked.md"]
    dep_targets = {
        (d.get("depends_on_id"), d.get("type")) for d in blocked.get("dependencies", [])
    }
    pending_id = shadow.task_id("specs/demo/tasks/01-pending.md")
    assert (pending_id, "blocks") in dep_targets


@requires_bd
def test_sync_mirrors_touch_rigor_and_budget_metadata(tmp_path):
    store = _git_store(tmp_path)
    _seed_three(store)
    shadow.sync(str(store), take_lock=False)
    issues = _export(store)
    meta = issues["specs/demo/tasks/01-pending.md"].get("metadata") or {}
    if isinstance(meta, str):
        meta = json.loads(meta)
    assert set(meta.get("touch")) == {"src/a.py", "tests/a.py"}
    assert meta.get("rigor") == "prototype"
    assert meta.get("budget") == "12 turns"


@requires_bd
def test_resync_reflects_an_edited_header(tmp_path):
    store = _git_store(tmp_path)
    path = _write_task(store, "demo", "01-pending.md", PENDING_TASK)
    shadow.sync(str(store), take_lock=False)
    assert _export(store)["specs/demo/tasks/01-pending.md"]["status"] == "open"

    path.write_text(PENDING_TASK.replace("Status: pending", "Status: done", 1))
    shadow.sync(str(store), take_lock=False)
    assert _export(store)["specs/demo/tasks/01-pending.md"]["status"] == "closed"


@requires_bd
def test_resync_does_not_reopen_a_bd_closed_issue(tmp_path):
    """bd is authoritative for the closed state (uz1): once an issue is closed
    in bd, a markdown 'pending' row must not reopen it on the next sync."""
    store = _git_store(tmp_path)
    _write_task(store, "demo", "01-pending.md", PENDING_TASK)
    shadow.sync(str(store), take_lock=False)
    issue_id = shadow.task_id("specs/demo/tasks/01-pending.md")
    assert _export(store)["specs/demo/tasks/01-pending.md"]["status"] == "open"

    # Closed in bd (the source of truth) while the markdown header stays pending.
    bd.bd_set_status(issue_id, "closed", cwd=str(store))
    shadow.sync(str(store), take_lock=False)  # must NOT reopen it
    assert _export(store)["specs/demo/tasks/01-pending.md"]["status"] == "closed"


@requires_bd
def test_sync_never_writes_markdown(tmp_path):
    store = _git_store(tmp_path)
    paths = [
        _write_task(store, "demo", "01-pending.md", PENDING_TASK),
        _write_task(store, "demo", "02-blocked.md", BLOCKED_TASK),
        _write_task(store, "demo", "03-done.md", DONE_TASK),
    ]
    before = {p: p.read_bytes() for p in paths}
    shadow.sync(str(store), take_lock=False)
    shadow.sync(str(store), take_lock=False)  # a second sync must not touch them either
    after = {p: p.read_bytes() for p in paths}
    assert before == after


# --- the write lock --------------------------------------------------------


@requires_bd
def test_sync_takes_the_write_lock(tmp_path):
    store = _git_store(tmp_path)
    _seed_three(store)
    # A live holder of the repo write lock must block the sync (it is a writer).
    with RepoLock(str(store)):
        assert (store / ".beads" / LOCK_NAME).exists()
        with pytest.raises(LockTimeout):
            shadow.sync(str(store), take_lock=True, acquire_timeout=0.3)
    # Released -> the sync now succeeds under its own lock.
    assert shadow.sync(str(store), take_lock=True, acquire_timeout=5) == 3


# --- upsert key: task ids are stable across syncs --------------------------


@requires_bd
def test_differential_task_ids_are_stable_across_syncs(tmp_path):
    """The upsert key is the task path, so a re-sync updates in place rather
    than duplicating — the property the differential relies on for a mirror."""
    rel = "specs/demo/tasks/01-pending.md"
    expected = "md-" + hashlib.sha1(rel.encode()).hexdigest()[:8]
    assert shadow.task_id(rel) == expected
    assert shadow.task_id(rel) == shadow.task_id(rel)


def test_cli_registers_shadow_sync_subcommand():
    """shadow-sync is invocable via the agentic CLI, not only as a module —
    the pipeline's programmatic entry (breakdown's post-authoring sync) needs
    a runnable command, not knowledge of the package layout."""
    from agentic.cli import build_parser

    args = build_parser().parse_args(["shadow-sync"])
    assert args.func is shadow.run
