#!/usr/bin/env python3
"""list_specs — quick per-repo spec status + next-command table.

Scans `specs/` under the current working directory, buckets every task by
status (R3), classifies each spec into exactly one next-command row per a
10-rule precedence order (R4), and prints one markdown table (R5) to
stdout. No arguments, no CLI flags (R6) — always scans `Path.cwd() / "specs"`.

See specs/list-specs/SPEC.md for the full requirements (R0-R6) this
implements.

Stdlib only. Read-only: never mutates anything it scans.
"""

import importlib.util
import sys
from pathlib import Path

_SCRIPT = Path(__file__).resolve()
_WORKBOARD_PY = _SCRIPT.parent.parent / "workboard" / "workboard.py"
_SPEC_READINESS_PY = _SCRIPT.parent.parent / "_shared" / "spec_readiness.py"


def _load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# Loading workboard.py this way executes its own top-level
# `sys.path.insert(0, .../_shared)` + `import viz`, so viz.py must keep
# importing cleanly. workboard's own CLI logic stays inert behind its
# `if __name__ == "__main__":` guard.
_workboard = _load_module("_list_specs_workboard", _WORKBOARD_PY)
scan_toolkit_specs = _workboard.scan_toolkit_specs
read_text = _workboard.read_text

_spec_readiness = _load_module("_list_specs_spec_readiness", _SPEC_READINESS_PY)
open_questions_unresolved = _spec_readiness.open_questions_unresolved


# ---------------------------------------------------------------- R3: bucketing

_PENDING_LIKE = {"pending", "open", "todo", "ready"}
_IN_PROGRESS_LIKE = {"in-progress", "in_progress", "claimed"}
_BLOCKED_OR_FAILED = {"blocked", "failed"}
_DONE_LIKE = {"done", "skipped"}


def bucket_status(status):
    """Classify one task's raw status string into exactly one of the R3
    disjoint categories. `scan_toolkit_specs` already defaults a missing
    `Status:` header to the literal string "pending", which falls into
    pending_like here — no separate "missing header" case is needed."""
    s = (status or "").lower()
    if s in _PENDING_LIKE:
        return "pending_like"
    if s in _IN_PROGRESS_LIKE:
        return "in_progress_like"
    if s == "deferred":
        return "deferred"
    if s in _BLOCKED_OR_FAILED:
        return "blocked_or_failed"
    if s == "draft":
        return "draft"
    if s in _DONE_LIKE:
        return "done_like"
    return "unrecognized"


# ---------------------------------------------------------------- R4: classify


def classify_spec(slug, tasks, open_questions_unresolved):
    """Classify one spec into exactly one next-command row (R4), first
    match wins. `tasks` is a list of dicts with at least "file" and
    "status" keys (the shape scan_toolkit_specs() produces per task).

    Returns {"slug": slug, "status": <summary string>,
             "next_command": <str or None>}.
    """
    if not tasks:
        # R3: tasks_total == 0 (missing or empty tasks/) skips bucketing.
        if open_questions_unresolved:
            return {
                "slug": slug,
                "status": "no tasks/",
                "next_command": f"/critique specs/{slug}/SPEC.md",
            }
        return {
            "slug": slug,
            "status": "no tasks/",
            "next_command": f"/breakdown specs/{slug}/SPEC.md",
        }

    buckets = {
        "pending_like": [],
        "in_progress_like": [],
        "deferred": [],
        "blocked_or_failed": [],
        "draft": [],
        "done_like": [],
        "unrecognized": [],
    }
    for t in tasks:
        buckets[bucket_status(t.get("status"))].append(t)

    n_deferred = len(buckets["deferred"])
    n_blocked = len(buckets["blocked_or_failed"])
    n_pending = len(buckets["pending_like"])
    n_in_progress = len(buckets["in_progress_like"])
    n_draft = len(buckets["draft"])
    n_unrecognized = len(buckets["unrecognized"])

    summary = (
        f"{len(tasks)} task(s): {n_pending} pending, {n_in_progress} "
        f"in-progress, {n_deferred} deferred, {n_blocked} blocked/failed, "
        f"{n_draft} draft, {len(buckets['done_like'])} done, "
        f"{n_unrecognized} unrecognized"
    )

    # Rule 1: >=1 task, deferred > 0 -> /drain (surfaces the batch interview).
    if n_deferred > 0:
        return {
            "slug": slug,
            "status": summary,
            "next_command": f"/drain specs/{slug}",
        }

    # Rule 2: deferred == 0, HUMAN-bounded blocked_or_failed > 0 -> flagged,
    # no command. Agent-bounded blockage (Unblock: run:/agent:) proceeds —
    # /drain owns the recheck — so it never gates a needs-attention flag;
    # only ask-typed or unblock-less blocked/failed tasks are the human's.
    agent_unblockable = [
        t
        for t in buckets["blocked_or_failed"]
        if (t.get("unblock") or {}).get("type") in ("run", "agent")
    ]
    n_human_blocked = n_blocked - len(agent_unblockable)
    if n_human_blocked > 0:
        return {
            "slug": slug,
            "status": f"{summary} — blocked/failed — needs attention "
            "(amend spec or attended /build)",
            "next_command": None,
        }

    # Rule 3: deferred == 0, blocked == 0, pending >= 2 -> /drain.
    if n_pending >= 2:
        return {
            "slug": slug,
            "status": summary,
            "next_command": f"/drain specs/{slug}",
        }

    # Rule 4: deferred == 0, blocked == 0, pending == 1 -> /build <file>.
    if n_pending == 1:
        return {
            "slug": slug,
            "status": summary,
            "next_command": f"/build {buckets['pending_like'][0]['file']}",
        }

    # Rule 5: deferred == 0, blocked == 0, pending == 0, in_progress > 0 ->
    # flagged, no command.
    if n_in_progress > 0:
        return {
            "slug": slug,
            "status": f"{summary} — in-progress/awaiting — check /fleet "
            "or a drain may be running",
            "next_command": None,
        }

    # Rule 5b: only agent-unblockable blocked/failed tasks remain open ->
    # /drain (it runs the recorded run:/agent: recheck steps).
    if agent_unblockable:
        return {
            "slug": slug,
            "status": f"{summary} — blocked task(s) agent-unblockable "
            "(Unblock: run/agent)",
            "next_command": f"/drain specs/{slug}",
        }

    # Rule 6: deferred, blocked, pending, in_progress, unrecognized all == 0
    # AND draft > 0 -> flagged, no command. (An unrecognized status anywhere
    # always outranks this — rule 7 catches that combination instead.)
    if n_unrecognized == 0 and n_draft > 0:
        return {
            "slug": slug,
            "status": f"{summary} — drafts ready for promotion "
            "(human: draft → pending)",
            "next_command": None,
        }

    # Rule 7 (R4's rule 9): every task is done_like -> /distill.
    if (
        n_deferred == 0
        and n_blocked == 0
        and n_pending == 0
        and n_in_progress == 0
        and n_draft == 0
        and n_unrecognized == 0
    ):
        return {
            "slug": slug,
            "status": summary,
            "next_command": "/distill",
        }

    # Rule 8 (R4's rule 10): anything left over — any state with
    # unrecognized > 0 that the above didn't already match, including
    # unrecognized coexisting with draft.
    return {
        "slug": slug,
        "status": f"{summary} — unrecognized task status — needs manual check",
        "next_command": None,
    }


# ---------------------------------------------------------------- scan + render


def scan_and_classify(repo_root):
    """R1/R2/R3/R4 end to end: scan specs/ under repo_root, skip archive/
    non-spec dirs (scan_toolkit_specs already requires SPEC.md to be a
    file), and classify each remaining spec. Returns rows sorted
    alphabetically by slug (R5)."""
    specs = scan_toolkit_specs(Path(repo_root))
    rows = []
    for s in specs:
        spec_md_path = Path(repo_root) / s["path"]
        text = read_text(spec_md_path)
        unresolved = open_questions_unresolved(text)
        tasks = [{"file": t["file"], "status": t["status"]} for t in s["tasks"]]
        rows.append(classify_spec(s["slug"], tasks, unresolved))
    rows.sort(key=lambda r: r["slug"])
    return rows


def render_table(rows):
    """R5: one markdown table, columns Spec | Status | Next command."""
    lines = [
        "| Spec | Status | Next command |",
        "| --- | --- | --- |",
    ]
    for r in rows:
        next_cmd = f"`{r['next_command']}`" if r["next_command"] else "—"
        lines.append(f"| {r['slug']} | {r['status']} | {next_cmd} |")
    return "\n".join(lines)


def run(repo_root):
    """R1: no specs/ directory -> one-line message, sys.exit(0)."""
    specs_dir = Path(repo_root) / "specs"
    if not specs_dir.is_dir():
        print("no specs/ directory found")
        sys.exit(0)
    rows = scan_and_classify(repo_root)
    print(render_table(rows))


def main():
    run(Path.cwd())


if __name__ == "__main__":
    main()
