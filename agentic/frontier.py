"""The dispatch frontier over bd tracker state.

Computes, from a single ``bd export`` read (all statuses, dependencies, and
``touch`` metadata in one call), the set of tasks an agent may run next:
open tasks whose blocking dependencies are all done, ordered by priority and
unblocking power, admitted greedily so no two admitted tasks — and no
admitted task and any in-progress (claimed) task — share a Touch path.

The Touch-disjointness predicate and the ordering are ported verbatim in
behavior from ``.claude/skills/drain/drain_frontier.py`` and
``.claude/skills/_shared/touch_disjoint.py`` (glob-prefix conflict,
conservative on ambiguity; priority then -unblocking_power then id). bd is
read only through the task-02 ``agentic.bd`` helpers; nothing here shells out
to bd directly.
"""

import json
import re

from agentic import bd

# A task is "done" when bd has closed it. "done" is accepted defensively for
# any imported JSONL that spells it that way.
_DONE_STATUSES = {"closed", "done"}
# Dependency types that gate readiness. bd's battery (SPEC "Graph and
# ready-work") pins these two as blocking; discovered-from and the rest are
# non-blocking.
_BLOCKING_DEP_TYPES = {"blocks", "parent-child"}

_GLOB_META_RE = re.compile(r"[*?\[]")


def literal_prefix(entry):
    """The literal prefix of a Touch entry up to its first glob metacharacter."""
    m = _GLOB_META_RE.search(entry)
    return entry[: m.start()] if m else entry


def pair_conflicts(a, b):
    """Two Touch entries conflict when either literal prefix is a prefix of the
    other. Ambiguity (a glob prefix that is itself a prefix of a concrete path)
    resolves to conflict — conservative, matching drain_frontier.py."""
    pa, pb = literal_prefix(a), literal_prefix(b)
    return pa.startswith(pb) or pb.startswith(pa)


def entries_disjoint(set_a, set_b):
    """True iff no entry in ``set_a`` conflicts with any entry in ``set_b``."""
    return not any(pair_conflicts(a, b) for a in set_a for b in set_b)


def status_of(issue):
    return (issue.get("status") or "").lower()


def is_done(issue):
    return status_of(issue) in _DONE_STATUSES


def priority_of(issue):
    """bd's integer priority (0 highest); missing/non-int defaults to P2 (2)."""
    p = issue.get("priority")
    return p if isinstance(p, int) else 2


def issue_touch(issue):
    """The set of Touch paths declared in a bd issue's ``touch`` metadata."""
    meta = issue.get("metadata") or {}
    raw = meta.get("touch") or []
    if isinstance(raw, str):
        raw = [raw]
    return {str(e).strip() for e in raw if str(e).strip()}


def _blocker_ids(issue):
    """The depends-on ids of this issue's blocking dependency edges."""
    out = []
    for dep in issue.get("dependencies") or []:
        if (dep.get("type") or "blocks") in _BLOCKING_DEP_TYPES:
            tid = dep.get("depends_on_id") or dep.get("to")
            if tid:
                out.append(tid)
    return out


def load_issues(cwd=None):
    """Every tracked issue as a dict, from one ``bd export`` (all statuses)."""
    raw = bd.bd_export(cwd=cwd) or ""
    issues = []
    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        obj = json.loads(line)
        if "id" not in obj:
            continue
        issues.append(obj)
    return issues


def compute_frontier(issues):
    """Return ``{dispatchable, admissible, claimed}`` for the given issues.

    - ``claimed``: in-progress issues (the in-flight claims).
    - ``dispatchable``: open issues whose blocking deps are all done, ordered
      by (priority, -unblocking_power, id).
    - ``admissible``: the greedy Touch-disjoint prefix of ``dispatchable``,
      seeded with the claimed issues' Touch footprint — the ready frontier.
    """
    by_id = {i["id"]: i for i in issues if "id" in i}

    claimed = [i for i in issues if status_of(i) == "in_progress"]
    claim_touch = set()
    for c in claimed:
        claim_touch |= issue_touch(c)

    open_issues = [i for i in issues if status_of(i) == "open"]

    # Reverse edge map for unblocking power: blocker id -> dependent open ids.
    dependents = {}
    for i in open_issues:
        for b in _blocker_ids(i):
            dependents.setdefault(b, set()).add(i["id"])

    dispatchable = []
    for i in open_issues:
        blocked = False
        for b in _blocker_ids(i):
            tgt = by_id.get(b)
            if tgt is None or not is_done(tgt):
                blocked = True
                break
        if not blocked:
            dispatchable.append(i)

    def unblocking_power(i):
        return len(dependents.get(i["id"], ()))

    dispatchable.sort(key=lambda i: (priority_of(i), -unblocking_power(i), i["id"]))

    admissible = []
    admitted_touch = set(claim_touch)
    for cand in dispatchable:
        ct = issue_touch(cand)
        if not entries_disjoint(ct, admitted_touch):
            continue
        admissible.append(cand)
        admitted_touch |= ct

    return {
        "dispatchable": dispatchable,
        "admissible": admissible,
        "claimed": claimed,
    }
