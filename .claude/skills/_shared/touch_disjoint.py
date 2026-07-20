"""Shared glob-prefix Touch-disjointness predicate for the toolkit's own
skill scripts (specs/drain-multi-spec-swarm R14).

`.claude/skills/drain/admission.py` uses this to compute each candidate
spec's Touch footprint (the union of its dispatchable tasks' `Touch:`
headers, read directly from the task files on disk — never from a
`drain_frontier.py` JSON field, which carries no per-task Touch data) and to
test pairwise cross-spec disjointness for spec-lease claiming (R1).

The algorithm is pinned to match `.claude/skills/drain/drain_frontier.py`'s
own internal Touch-disjointness check exactly
(specs/drain-frontier-scanner/SPEC.md R1), so the two scripts cannot silently
diverge on the conservative-ambiguity direction and co-admit a real cross-spec
collision: normalize each entry to its literal prefix up to the first glob
metacharacter; two entries conflict when either literal prefix is a prefix of
the other; ambiguity resolves to "not disjoint" (conservative). The two
copies are intentionally independent for now — docs/TASKS.md tracks the
follow-up to converge them onto this single helper.

Reached the same way workboard reaches `viz`/`spec_readiness`/`headers`:
`sys.path.insert(0, <.../_shared>)` then `import touch_disjoint`.

Stdlib only; no side effects on import beyond compiling the regexes.
"""

import re
from pathlib import Path

_GLOB_META_RE = re.compile(r"[*?\[]")
_TOUCH_RE = re.compile(r"^Touch:\s*(.*)$", re.MULTILINE)


def literal_prefix(entry):
    """The literal prefix of a Touch entry up to its first glob metacharacter."""
    m = _GLOB_META_RE.search(entry)
    return entry[: m.start()] if m else entry


def pair_conflicts(a, b):
    """Two Touch entries conflict when either literal prefix is a prefix of the
    other. Ambiguity (a glob prefix that is itself a prefix of a concrete path)
    resolves to conflict — conservative, per drain_frontier.py and the per-spec
    lesson in docs/memory/drain-dispatch-lessons.md."""
    pa, pb = literal_prefix(a), literal_prefix(b)
    return pa.startswith(pb) or pb.startswith(pa)


def entries_disjoint(set_a, set_b):
    """True iff no entry in set_a conflicts with any entry in set_b."""
    return not any(pair_conflicts(a, b) for a in set_a for b in set_b)


def parse_touch(text):
    """The set of `Touch:` entries declared in a task file's text (comma-split,
    stripped). No `Touch:` header -> the empty set."""
    m = _TOUCH_RE.search(text)
    if not m:
        return set()
    return {e.strip() for e in m.group(1).split(",") if e.strip()}


def footprint(task_file_paths):
    """The union of `Touch:` entries across the given task files, read from
    disk. This is a spec's dispatchable-task Touch footprint when passed that
    spec's dispatchable task file paths (R14: sourced from files, not JSON)."""
    fp = set()
    for path in task_file_paths:
        try:
            text = Path(path).read_text(encoding="utf-8")
        except OSError:
            text = ""
        fp |= parse_touch(text)
    return fp
