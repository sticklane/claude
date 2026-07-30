# Task 05: bin/drain-report — the computed run report

<!-- Registration fields (Depends on, Budget, Touch, Rigor) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. Status and Priority are frozen authoring-time display only: bd owns their live values. -->

Status: pending
Depends on: 04
Priority: P1
Budget: 40 turns
Spec: ../SPEC.md (requirements EP6, decisions D3, D6)
Touch: bin/drain-report, tests/test_drain_report.sh, tests/inventory/drain-economy.json, specs/toolkit-core-simplification/surface-inventory/drain-economy.json

## Goal

`bin/drain-report <run-bead-id>` prints a run's accounting from bd and the run
log alone, with zero model calls. It leads with focus status — the focus
feature and its acceptance delta, blocked-on-you items first, spillover events
with reasons — then closed (listed), opened-blocking, opened-triage, declined,
deferred, imported blocking work, chores, discovered digest, net focus delta,
tokens-per-closure, trailing net burn over this focus's last 3 runs, and
projected passes-to-done. Tokens come from the workflow journal only; where no
journal exists the metric is omitted, never estimated. The projection is
suppressed below 2 data points.

## Touch

This script reads; it never writes bd state and never edits a spec. It consumes
task 04's run-bead body and run-log grammar and task 03's `triage` /
`declined-at-triage` labels — parse them, do not redefine them. The acceptance
delta it prints comes from `acceptance-status.json` when task 08's `bin/spec-gate`
has written one; absent that file the report says so and omits the delta rather
than computing a fallback number. It must NOT render a live view (task 06's
`bin/drain-watch`) or touch drain's SKILL.md.

## Steps

1. Write the failing test first: `tests/test_drain_report.sh` over `mktemp -d`
   fixtures holding a synthetic bd export and run log with hand-computed
   deltas. Assert on parsed structure — section order, the presence and
   position of each section, and the numbers — never on exact sentence text.
2. Cover the arithmetic cases explicitly: a two-run fixture with known deltas
   prints `net burn` and `passes-to-done` matching the hand-computed values; a
   one-run fixture prints neither; a run with no journal omits
   tokens-per-closure entirely.
3. Cover the ordering invariant: focus status is first and blocked-on-you items
   precede everything else within it, regardless of how the fixture orders the
   underlying issues.
4. Implement `bin/drain-report`, matching the language and style of the
   existing `bin/` scripts. Every number derives from bd, the run log, and
   `acceptance-status.json`; there is no model call and no network access.
5. Degrade per missing source rather than failing: a missing journal, a missing
   `acceptance-status.json`, or a single-run history each suppress their own
   line and nothing else.
6. Bugs get a phase pointer, never a fraction (D6) — where the report would
   print proximity for a bug-labelled bead before `fix-verified`, print the
   phase instead. Task 09 owns the phase metadata; consume it if present and
   omit the line if not.
7. Register the new script and test in the surface and test inventories.

## Acceptance

- [ ] `bash tests/test_drain_report.sh` → exits 0, reports 0 failures. **L2**
- [ ] Two-run fixture: `bin/drain-report <fixture-id> | grep -c 'net burn'` → 1
      and the printed value equals the hand-computed one asserted in the test;
      one-run fixture: `bin/drain-report <fixture-id> | grep -c 'net burn\|passes-to-done'`
      → 0. **L2**
- [ ] No-journal fixture: `bin/drain-report <fixture-id> | grep -ci 'tokens'`
      → 0, proving the metric is omitted rather than estimated. **L2**
- [ ] `bin/drain-report <spillover-fixture-id> | head -20 | grep -n 'blocked-on-you' | cut -d: -f1`
      → a line number smaller than that of any other section header, proving
      the lead-with-focus ordering. **L2**
- [ ] `grep -rc 'claude\|Agent(' bin/drain-report` → 0, proving zero model
      calls (D3). **L1**
- [ ] `python3 scripts/inventory-core-surface.py --root . --check specs/toolkit-core-simplification/BASELINE.json 2>&1 | grep -c 'unclassified\|drift'` → 0. **L2**
- [ ] `bash scripts/check.sh` → `check.sh: green`. **L2**
