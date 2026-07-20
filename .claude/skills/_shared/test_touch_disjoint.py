#!/usr/bin/env python3
"""Tests for touch_disjoint — the shared glob-prefix Touch-disjointness
predicate (specs/drain-multi-spec-swarm R14).

Self-running: `python3 test_touch_disjoint.py` runs every case, prints one
line per case, and exits non-zero on the first failure (there is no central
pytest runner in this repo — the acceptance invokes this file directly).

The predicate MUST match `.claude/skills/drain/drain_frontier.py`'s own
internal check exactly (specs/drain-frontier-scanner/SPEC.md R1): normalize
each entry to its literal prefix up to the first glob metacharacter; two
entries conflict when either prefix is a prefix of the other; ambiguity
resolves to "not disjoint" (conservative). See
specs/drain-multi-spec-swarm/tasks/04-admission-module.md.
"""

import sys
import tempfile
from pathlib import Path

from touch_disjoint import (
    entries_disjoint,
    footprint,
    literal_prefix,
    pair_conflicts,
    parse_touch,
)


def test_literal_prefix_stops_at_first_glob_meta():
    assert literal_prefix("src/app/main.py") == "src/app/main.py"
    assert literal_prefix("src/*.py") == "src/"
    assert literal_prefix("a/b?/c") == "a/b"
    assert literal_prefix("a/[abc]/c") == "a/"


def test_disjoint_footprints_report_disjoint():
    assert entries_disjoint({"src/a.py"}, {"src/b.py", "docs/x.md"}) is True


def test_overlapping_footprints_report_conflict():
    assert entries_disjoint({"src/a.py"}, {"src/a.py"}) is False
    assert entries_disjoint({"src/a.py", "lib/z"}, {"lib/z"}) is False


def test_ambiguous_prefix_resolves_to_not_disjoint():
    # A glob's literal prefix is itself a prefix of a concrete path in the
    # other set: whether the glob actually matches that path is undecidable
    # from prefixes alone, so the conservative resolution is NOT disjoint.
    # drain_frontier.py resolves this identically (startswith either way).
    assert pair_conflicts("src/*", "src/app/main.py") is True
    assert entries_disjoint({"src/*"}, {"src/app/main.py"}) is False
    # symmetric — order of the two sets must not change the verdict
    assert entries_disjoint({"src/app/main.py"}, {"src/*"}) is False
    # it must never wrongly clear the ambiguous case as disjoint
    assert entries_disjoint({"src/*"}, {"src/app/main.py"}) is not True


def test_footprint_reads_touch_headers_from_disk_not_json():
    # R14 boundary: footprint sources Touch: from task FILES on disk, never
    # from a drain_frontier.py JSON field.
    with tempfile.TemporaryDirectory() as d:
        t1 = Path(d) / "01-a.md"
        t2 = Path(d) / "02-b.md"
        t1.write_text(
            "# Task\n\nStatus: pending\nTouch: src/a.py, lib/z\n", encoding="utf-8"
        )
        t2.write_text("# Task\n\nStatus: pending\nTouch: docs/x.md\n", encoding="utf-8")
        fp = footprint([str(t1), str(t2)])
        assert fp == {"src/a.py", "lib/z", "docs/x.md"}


def test_parse_touch_missing_header_is_empty():
    assert parse_touch("# Task\n\nStatus: pending\n") == set()


_CASES = [
    (
        "literal_prefix stops at first glob metacharacter",
        test_literal_prefix_stops_at_first_glob_meta,
    ),
    ("disjoint footprints report disjoint", test_disjoint_footprints_report_disjoint),
    (
        "overlapping footprints report conflict",
        test_overlapping_footprints_report_conflict,
    ),
    (
        "ambiguous prefix resolves to NOT disjoint (conservative)",
        test_ambiguous_prefix_resolves_to_not_disjoint,
    ),
    (
        "footprint reads Touch: headers from disk, not JSON (R14)",
        test_footprint_reads_touch_headers_from_disk_not_json,
    ),
    (
        "parse_touch on a file with no Touch: header is empty",
        test_parse_touch_missing_header_is_empty,
    ),
]


def _run():
    for name, fn in _CASES:
        try:
            fn()
        except AssertionError as exc:
            print(f"FAIL: {name}: {exc}", file=sys.stderr)
            return 1
        print(f"ok: {name}")
    print(f"all {len(_CASES)} touch_disjoint cases passed")
    return 0


if __name__ == "__main__":
    sys.exit(_run())
