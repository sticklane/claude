"""SPEC S3 / R-L: ``agentic ready`` lists tasks whose blockers are done and
whose Touch paths do not overlap any claimed task, priority-ordered.

The Touch-disjoint co-admission and ordering are ported from
``.claude/skills/drain/drain_frontier.py`` and ``_shared/touch_disjoint.py``
onto bd tracker state, read only through the task-02 ``agentic.bd`` helpers.

Fixtures seed a real bd store (``bd_init`` + ``bd_import`` of a crafted
JSONL) and drive the real ``agentic ready`` command, so the tests exercise
bd's actual ready/blocker/metadata behavior rather than a mock.
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

from agentic import bd, frontier  # noqa: E402

requires_bd = pytest.mark.skipif(
    bd.bd_which() is None, reason="bd not installed on PATH"
)


def _issue(
    id_, title, status="open", priority=1, touch=None, owner=None, blocked_by=None
):
    row = {
        "id": id_,
        "title": title,
        "status": status,
        "priority": priority,
        "issue_type": "task",
        "metadata": {"touch": list(touch or [])},
    }
    if owner is not None:
        row["owner"] = owner
    if blocked_by is not None:
        row["dependencies"] = [
            {"issue_id": id_, "depends_on_id": blocked_by, "type": "blocks"}
        ]
    return row


def _seed(tmp_path, rows):
    """A fresh bd store seeded via the task-02 helpers; returns its dir."""
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


def _ready_ids(store):
    r = _agentic(store, "ready", "--json")
    assert r.returncode == 0, r.stderr
    return [t["id"] for t in json.loads(r.stdout)]


# --- Touch predicate port (unit, no bd) ------------------------------------


def test_touch_disjointness_matches_the_conservative_glob_prefix_port():
    assert frontier.entries_disjoint({"agentic/ready.py"}, {"tests/x.py"})
    # a glob prefix that is itself a prefix of a concrete path -> conflict
    assert not frontier.entries_disjoint({"agentic/*.py"}, {"agentic/ready.py"})
    # directory prefix conflicts with a file beneath it
    assert not frontier.entries_disjoint({"src/"}, {"src/a.py"})
    # empty footprints never conflict
    assert frontier.entries_disjoint(set(), {"anything"})


def test_frontier_blocks_issue_when_dependency_is_missing():
    issues = [
        _issue(
            "pr-orphan",
            "missing dependency",
            touch=["src/orphan.py"],
            blocked_by="pr-missing",
        )
    ]

    result = frontier.compute_frontier(issues)

    assert result["dispatchable"] == []
    assert result["admissible"] == []


@pytest.mark.parametrize(
    "retired_path",
    [
        ".claude/skills/drain/drain_frontier.py",
        ".claude/skills/drain/test_drain_frontier.py",
        ".claude/skills/drain/fixtures/basic-window",
    ],
)
def test_markdown_frontier_assets_remain_retired(retired_path):
    assert not (REPO_ROOT / retired_path).exists()


# --- ready command ---------------------------------------------------------


@requires_bd
def test_ready_excludes_task_whose_blocker_is_not_done(tmp_path):
    store = _seed(
        tmp_path,
        [
            _issue("pr-block", "open blocker", priority=0, touch=["src/x.py"]),
            _issue(
                "pr-dep",
                "blocked by open blocker",
                priority=0,
                touch=["src/y.py"],
                blocked_by="pr-block",
            ),
        ],
    )
    ids = _ready_ids(store)
    assert "pr-dep" not in ids  # its blocker is still open
    assert "pr-block" in ids  # the unblocked blocker is itself ready


@requires_bd
def test_ready_includes_task_once_its_blocker_is_done(tmp_path):
    store = _seed(
        tmp_path,
        [
            _issue("pr-done", "closed blocker", status="closed", touch=["src/x.py"]),
            _issue(
                "pr-go",
                "unblocked now",
                touch=["src/y.py"],
                blocked_by="pr-done",
            ),
        ],
    )
    ids = _ready_ids(store)
    assert "pr-go" in ids  # blocker is closed -> ready


@requires_bd
def test_ready_excludes_open_task_overlapping_a_claimed_task(tmp_path):
    store = _seed(
        tmp_path,
        [
            _issue(
                "pr-claim",
                "in flight",
                status="in_progress",
                priority=0,
                touch=["agentic/ready.py"],
            ),
            _issue(
                "pr-overlap",
                "overlaps the claim",
                priority=0,
                touch=["agentic/ready.py"],
            ),
            _issue("pr-free", "disjoint", priority=0, touch=["agentic/other.py"]),
        ],
    )
    ids = _ready_ids(store)
    assert "pr-overlap" not in ids  # Touch overlaps the claimed task
    assert "pr-free" in ids  # disjoint from the claim -> kept
    assert "pr-claim" not in ids  # in_progress is never "ready"


@requires_bd
def _epic(id_, title, priority=1):
    return {
        "id": id_,
        "title": title,
        "status": "open",
        "priority": priority,
        "issue_type": "epic",
        "metadata": {},
    }


def _child_of(issue, epic_id):
    """Attach a parent-child edge from a task issue to its epic."""
    issue.setdefault("dependencies", []).append(
        {"issue_id": issue["id"], "depends_on_id": epic_id, "type": "parent-child"}
    )
    return issue


@requires_bd
def test_ready_never_offers_an_epic_as_work(tmp_path):
    """An epic groups work; it is not itself dispatchable."""
    store = _seed(
        tmp_path,
        [
            _epic("ep-a", "Epic: feature A", priority=0),
            _child_of(_issue("t-a1", "task a1", priority=2, touch=["a.py"]), "ep-a"),
        ],
    )
    ids = _ready_ids(store)
    assert "ep-a" not in ids
    assert "t-a1" in ids


@requires_bd
def test_ready_drains_the_highest_priority_epic_before_a_lower_one(tmp_path):
    """Epic priority outranks task priority, so a feature drains as a unit.

    Without grouping, b-hi (P0) would lead the flat queue. Its epic is P1, so
    every task of the P0 epic comes first — the point of the epic bead.
    """
    store = _seed(
        tmp_path,
        [
            _epic("ep-hi", "Epic: high", priority=0),
            _epic("ep-lo", "Epic: low", priority=1),
            _child_of(_issue("a-lo", "a low", priority=3, touch=["a.py"]), "ep-hi"),
            _child_of(_issue("b-hi", "b high", priority=0, touch=["b.py"]), "ep-lo"),
        ],
    )
    order = _ready_ids(store)
    assert order.index("a-lo") < order.index("b-hi")


@requires_bd
def test_ready_keeps_one_epics_tasks_contiguous(tmp_path):
    """Tasks of the same epic are not interleaved with another epic's."""
    store = _seed(
        tmp_path,
        [
            _epic("ep-1", "Epic: one", priority=0),
            _epic("ep-2", "Epic: two", priority=1),
            _child_of(_issue("x1", "x1", priority=0, touch=["x1.py"]), "ep-1"),
            _child_of(_issue("x2", "x2", priority=3, touch=["x2.py"]), "ep-1"),
            _child_of(_issue("y1", "y1", priority=0, touch=["y1.py"]), "ep-2"),
        ],
    )
    order = _ready_ids(store)
    assert order.index("x1") < order.index("x2") < order.index("y1")


@requires_bd
def test_ready_ranks_unparented_task_by_its_own_priority(tmp_path):
    """Janitorial work carries no epic, so a P0 chore still beats a P1 feature."""
    store = _seed(
        tmp_path,
        [
            _epic("ep-f", "Epic: feature", priority=1),
            _child_of(_issue("f1", "feature task", priority=0, touch=["f.py"]), "ep-f"),
            _issue("chore", "janitorial", priority=0, touch=["c.py"]),
        ],
    )
    order = _ready_ids(store)
    assert order.index("chore") < order.index("f1")


@requires_bd
def test_ready_orders_higher_priority_first(tmp_path):
    store = _seed(
        tmp_path,
        [
            _issue("pr-lo", "low", priority=2, touch=["src/a.py"]),
            _issue("pr-hi", "high", priority=0, touch=["src/b.py"]),
        ],
    )
    order = _ready_ids(store)
    assert order.index("pr-hi") < order.index("pr-lo")  # P0 before P2


@requires_bd
def test_ready_breaks_priority_tie_by_unblocking_power(tmp_path):
    store = _seed(
        tmp_path,
        [
            _issue("pr-a", "no dependents", priority=1, touch=["src/a.py"]),
            _issue("pr-z", "unblocks work", priority=1, touch=["src/z.py"]),
            _issue(
                "pr-child",
                "blocked child",
                priority=1,
                touch=["src/child.py"],
                blocked_by="pr-z",
            ),
        ],
    )

    ids = _ready_ids(store)

    assert ids.index("pr-z") < ids.index("pr-a")


@requires_bd
def test_ready_breaks_remaining_tie_by_issue_id(tmp_path):
    store = _seed(
        tmp_path,
        [
            _issue("pr-z", "lexically later", priority=1, touch=["src/z.py"]),
            _issue("pr-a", "lexically earlier", priority=1, touch=["src/a.py"]),
        ],
    )

    ids = _ready_ids(store)

    assert ids == ["pr-a", "pr-z"]


@requires_bd
def test_ready_json_exposes_documented_fields(tmp_path):
    store = _seed(
        tmp_path,
        [
            _issue(
                "pr-one",
                "the one",
                priority=1,
                touch=["src/one.py", "tests/one.py"],
            ),
        ],
    )
    r = _agentic(store, "ready", "--json")
    assert r.returncode == 0, r.stderr
    data = json.loads(r.stdout)
    assert isinstance(data, list) and data
    item = next(t for t in data if t["id"] == "pr-one")
    assert {"id", "title", "priority", "touch"}.issubset(item)
    assert item["title"] == "the one"
    assert item["priority"] == 1
    assert set(item["touch"]) == {"src/one.py", "tests/one.py"}


@requires_bd
def test_ready_co_admits_disjoint_and_drops_mutual_overlap(tmp_path):
    # Two open, unclaimed, same-priority tasks with overlapping Touch: only
    # one is admitted; a disjoint task is always admitted.
    store = _seed(
        tmp_path,
        [
            _issue("pr-first", "first", priority=0, touch=["shared/mod.py"]),
            _issue("pr-second", "second", priority=0, touch=["shared/mod.py"]),
            _issue("pr-solo", "disjoint", priority=0, touch=["solo/x.py"]),
        ],
    )
    ids = _ready_ids(store)
    assert "pr-solo" in ids
    assert len({"pr-first", "pr-second"} & set(ids)) == 1


# --- resume command --------------------------------------------------------


@requires_bd
def test_resume_shows_frontier_and_in_flight_claims(tmp_path):
    store = _seed(
        tmp_path,
        [
            _issue(
                "pr-run",
                "being worked",
                status="in_progress",
                priority=0,
                touch=["a.py"],
                owner="alice",
            ),
            _issue("pr-next", "ready next", priority=1, touch=["b.py"]),
        ],
    )
    r = _agentic(store, "resume")
    assert r.returncode == 0, r.stderr
    out = r.stdout
    assert "pr-run" in out  # the in-flight claim (what)
    assert "being worked" in out
    assert "pr-next" in out  # the frontier
