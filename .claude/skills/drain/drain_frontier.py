#!/usr/bin/env python3
"""drain_frontier — deterministic dispatch frontier from task headers.

Reads one or more spec dirs' `tasks/*.md` headers plus each SPEC.md's
`## Parallelization` `- Group:` lines and emits a JSON frontier report to
stdout: `dispatchable` (the full ordered set of dispatchable tasks),
`admissible` (its windowed, co-admissible, Touch-disjoint subset), `blocked`
(unmet deps / `Unblock:` line / unresolved external dep), and `diagnostics`.

The script owns the loop and the gate; the model keeps every judgment call
it has today (verdict handling, deferral, BLOCKED routing, lease/baton,
merges). See specs/drain-frontier-scanner/SPEC.md (R1) for the pinned field
semantics and `.claude/skills/drain/reference.md`'s admission section for the
authority this restates.

Read-only. Stdlib only. Deterministic output ordering.
"""

import argparse
import json
import re
import sys
from pathlib import Path

# Bootstrap the shared header regexes the list_specs.py way: put _shared/ on
# sys.path, then a regular `import headers` (path-loading the loader would
# need a loader to load the loader).
_SCRIPT = Path(__file__).resolve()
sys.path.insert(0, str(_SCRIPT.parent.parent / "_shared"))
from headers import DEPENDS_RE, PRIORITY_RE, STATUS_RE  # noqa: E402

# Status vocabulary. A present `Status:` value outside this set is malformed
# (fatal); a missing `Status:` line defaults to "pending" (diagnostic, exit 0).
_PENDING = {"pending", "open", "todo", "ready"}
_DONE = {"done", "skipped"}
_KNOWN_STATUS = (
    _PENDING
    | _DONE
    | {
        "in-progress",
        "in_progress",
        "claimed",
        "deferred",
        "blocked",
        "failed",
        "needs-verification",
        "needs_verification",
    }
)

_STATUS_LINE_RE = re.compile(r"^Status:[ \t]*(.*)$", re.MULTILINE)
_TOUCH_RE = re.compile(r"^Touch:\s*(.*)$", re.MULTILINE)
_UNBLOCK_RE = re.compile(r"^Unblock:\s*(.*)$", re.MULTILINE)
_GROUP_RE = re.compile(r"^- Group:\s*(.*)$", re.MULTILINE)
_GLOB_META_RE = re.compile(r"[*?\[]")
_LEADING_NUM_RE = re.compile(r"^(\d+)")


class FrontierError(Exception):
    """Raised on a present-but-malformed mandatory header. A wrong frontier is
    worse than no frontier, so this aborts with a non-zero exit."""


def read_text(path):
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def _task_number(filename):
    """The leading integer of a task filename, or None (e.g. '02-x.md' -> 2)."""
    m = _LEADING_NUM_RE.match(filename)
    return int(m.group(1)) if m else None


def literal_prefix(entry):
    """The literal prefix of a Touch entry up to its first glob metacharacter."""
    m = _GLOB_META_RE.search(entry)
    return entry[: m.start()] if m else entry


def _pair_conflicts(a, b):
    """Two Touch entries conflict when either literal prefix is a prefix of the
    other (ambiguity resolves to conflict — conservative, per the per-spec
    lesson in docs/memory/drain-dispatch-lessons.md)."""
    pa, pb = literal_prefix(a), literal_prefix(b)
    return pa.startswith(pb) or pb.startswith(pa)


def entries_disjoint(set_a, set_b):
    """True iff no entry in set_a conflicts with any entry in set_b."""
    return not any(_pair_conflicts(a, b) for a in set_a for b in set_b)


def parse_touch(text):
    m = _TOUCH_RE.search(text)
    if not m:
        return set()
    return {e.strip() for e in m.group(1).split(",") if e.strip()}


def parse_groups(spec_text):
    """The `- Group:` lines under a SPEC.md's `## Parallelization`, each as a
    frozenset of task numbers."""
    groups = []
    for line in _GROUP_RE.findall(spec_text):
        nums = {int(t) for t in re.findall(r"\d+", line)}
        if nums:
            groups.append(frozenset(nums))
    return groups


def _parse_status(text, rel):
    """(status, defaulted?). Raises FrontierError on a malformed value."""
    line = _STATUS_LINE_RE.search(text)
    if line is None:
        return "pending", True
    raw = line.group(1).strip().strip("[]").strip()
    if not raw:
        return "pending", True
    value = raw.lower()
    m = STATUS_RE.search(text)
    if m is None or value not in _KNOWN_STATUS:
        raise FrontierError(f"{rel}: malformed Status value {raw!r}")
    return value, False


def _parse_priority(text):
    """(priority, defaulted?). Missing / out-of-range -> P2 (diagnostic)."""
    m = PRIORITY_RE.search(text)
    if m is None:
        return "P2", True
    return m.group(1).upper(), False


def _parse_deps(text, rel):
    """List of dep tokens ({'kind': 'number'|'path', ...}). Raises FrontierError
    on an unparseable reference."""
    m = DEPENDS_RE.search(text)
    if not m:
        return []
    raw = m.group(1).strip()
    if not raw or raw.lower() == "none":
        return []
    deps = []
    for entry in raw.split(","):
        e = entry.strip()
        if not e:
            continue
        if re.fullmatch(r"\d+", e):
            deps.append({"kind": "number", "raw": e, "num": int(e)})
        elif "/" in e or e.endswith(".md"):
            deps.append({"kind": "path", "raw": e})
        else:
            raise FrontierError(f"{rel}: unparseable Depends on reference {e!r}")
    return deps


def _load_tasks(spec_dirs):
    """Parse every task in every spec dir. Returns (tasks, diagnostics).

    Each task: {path, spec, num, filename, status, priority, priority_default,
    status_default, deps, touch, unblock}. Raises FrontierError on a malformed
    mandatory header.
    """
    tasks = []
    diagnostics = []
    for sd in spec_dirs:
        spec_dir = Path(sd)
        tasks_dir = spec_dir / "tasks"
        if not tasks_dir.is_dir():
            continue
        for tf in sorted(tasks_dir.glob("*.md")):
            rel = str(tf)
            text = read_text(tf)
            status, status_default = _parse_status(text, rel)
            priority, priority_default = _parse_priority(text)
            deps = _parse_deps(text, rel)
            if status_default:
                diagnostics.append(
                    {
                        "path": rel,
                        "kind": "default",
                        "field": "Status",
                        "applied": "pending",
                    }
                )
            if priority_default:
                diagnostics.append(
                    {
                        "path": rel,
                        "kind": "default",
                        "field": "Priority",
                        "applied": "P2",
                    }
                )
            tasks.append(
                {
                    "path": rel,
                    "spec": str(spec_dir),
                    "num": _task_number(tf.name),
                    "filename": tf.name,
                    "status": status,
                    "priority": priority,
                    "deps": deps,
                    "touch": parse_touch(text),
                    "unblock": (
                        _UNBLOCK_RE.search(text).group(1).strip()
                        if _UNBLOCK_RE.search(text)
                        else None
                    ),
                }
            )
    return tasks, diagnostics


def _resolve_dep(dep, task, by_spec_num, all_by_path):
    """Resolve a dep to a scanned task, or None if it points outside the scan.

    A within-spec number resolves against the dep-owner's own spec; a path
    resolves against the union of scanned task paths (so a cross-spec path is
    resolved only when its target spec is also scanned)."""
    if dep["kind"] == "number":
        return by_spec_num.get((task["spec"], dep["num"]))
    target = (Path(task["path"]).parent / dep["raw"]).resolve()
    return all_by_path.get(str(target))


def compute_frontier(spec_dirs, window, claimed):
    """Compute the frontier report dict. Raises FrontierError on a malformed
    mandatory header (the caller maps it to a non-zero exit)."""
    tasks, diagnostics = _load_tasks(spec_dirs)

    by_spec_num = {(t["spec"], t["num"]): t for t in tasks if t["num"] is not None}
    all_by_path = {str(Path(t["path"]).resolve()): t for t in tasks}

    # Claim set: the union of Touch footprints of the in-flight --claimed tasks.
    claim_touch = set()
    for c in claimed or []:
        claim_touch |= parse_touch(read_text(Path(c)))

    # Classify each task; collect unblocking-power inputs.
    pending = [t for t in tasks if t["status"] in _PENDING]
    blocked = []
    dispatchable_tasks = []

    for t in pending:
        unmet = []
        unresolved = []
        for dep in t["deps"]:
            resolved = _resolve_dep(dep, t, by_spec_num, all_by_path)
            if resolved is None:
                unresolved.append(dep["raw"])
            elif resolved["status"] not in _DONE:
                unmet.append(dep["raw"])
        if unresolved:
            for u in unresolved:
                diagnostics.append(
                    {"path": t["path"], "kind": "unresolved-external-dep", "dep": u}
                )
            blocked.append(
                {
                    "path": t["path"],
                    "reason": "unresolved-external-dep",
                    "deps": unresolved,
                }
            )
        elif unmet:
            blocked.append({"path": t["path"], "reason": "unmet-deps", "deps": unmet})
        else:
            dispatchable_tasks.append(t)

    # Status-blocked tasks carry their Unblock: line.
    for t in tasks:
        if t["status"] in {"blocked", "failed"}:
            blocked.append(
                {"path": t["path"], "reason": "unblock", "unblock": t["unblock"]}
            )

    # Unblocking-power: count of still-pending tasks whose deps name this task.
    def unblocking_power(t):
        if t["num"] is None:
            return 0
        n = 0
        for other in pending:
            if other is t:
                continue
            for dep in other["deps"]:
                if (
                    dep["kind"] == "number"
                    and dep["num"] == t["num"]
                    and other["spec"] == t["spec"]
                ):
                    n += 1
                    break
        return n

    def prio_num(p):
        return int(p[1:])

    dispatchable_tasks.sort(
        key=lambda t: (prio_num(t["priority"]), -unblocking_power(t), t["path"])
    )

    def entry(t):
        return {
            "path": t["path"],
            "priority": t["priority"],
            "rationale": (
                f"priority={t['priority']} unblocking_power={unblocking_power(t)}"
            ),
        }

    dispatchable = [entry(t) for t in dispatchable_tasks]

    # Admissible: per-spec, empty-window co-admission + Touch disjointness from
    # the claim set (--claimed plus tasks already admitted this pass). The
    # scanner assumes an empty window; drain applies the live-window gate.
    admissible_tasks = []
    by_spec = {}
    for t in dispatchable_tasks:
        by_spec.setdefault(t["spec"], []).append(t)

    for sd in spec_dirs:  # per-spec, in argument order; never interleaved
        spec = str(Path(sd))
        spec_tasks = by_spec.get(spec, [])
        if not spec_tasks:
            continue
        groups = parse_groups(read_text(Path(sd) / "SPEC.md"))

        def co_admissible(a, b):
            return any(a["num"] in g and b["num"] in g for g in groups)

        admitted = []
        admitted_touch = set(claim_touch)
        for cand in spec_tasks:
            if admitted and not all(co_admissible(cand, a) for a in admitted):
                continue
            if not entries_disjoint(cand["touch"], admitted_touch):
                continue
            admitted.append(cand)
            admitted_touch |= cand["touch"]
        admissible_tasks.extend(admitted)

    if window is not None:
        admissible_tasks = admissible_tasks[:window]
    admissible = [entry(t) for t in admissible_tasks]

    return {
        "dispatchable": dispatchable,
        "admissible": admissible,
        "blocked": blocked,
        "diagnostics": diagnostics,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Deterministic drain dispatch frontier from task headers."
    )
    parser.add_argument("spec_dirs", nargs="+", help="one or more spec dirs")
    parser.add_argument(
        "--window",
        type=int,
        default=None,
        help="truncate admissible to N (reporting cap only)",
    )
    parser.add_argument(
        "--claimed",
        nargs="*",
        default=[],
        help="in-flight task paths whose Touch forms the claim set",
    )
    args = parser.parse_args(argv)
    try:
        frontier = compute_frontier(args.spec_dirs, args.window, args.claimed)
    except FrontierError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    json.dump(frontier, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
