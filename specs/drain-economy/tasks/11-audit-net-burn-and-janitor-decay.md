# Task 11: the net-burn audit class and janitor's triage decay

<!-- Registration fields (Depends on, Budget, Touch, Rigor) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. Status and Priority are frozen authoring-time display only: bd owns their live values. -->

Status: pending
Depends on: 04
Priority: P2
Budget: 35 turns
Spec: ../SPEC.md (requirements EP9, EP10)
Touch: agentic/audit.py, bin/janitor, tests/test_agentic_audit.py, tests/test_janitor_triage.sh, tests/inventory/drain-economy-11.json

## Goal

Two backstops keep the queue from growing quietly. `agentic audit` gains a
regression class computed from `drain-run` beads — opened-admitted (blocking
plus promoted) minus closed, per run — that files one deduplicated bead naming
the focus and the ratio when the sum over 3 consecutive runs of a single focus
is positive. `janitor --scope triage` closes `triage` items untouched for
`TRIAGE_DECAY_DAYS` (default 14), labels them `triage-archived`, honors
`--dry-run`, and counts in janitor's summary.

## Touch

Both edits are additive: one new class in `REGRESSION_CLASSES`' existing filing
machinery, one new scope in janitor's existing scope switch. Neither rewrites
its host's structure, and neither touches drain's SKILL.md.

The decay half shares one convention with task 03's decline half — close the
bead, label why it died. Task 03 defines `declined-at-triage`; this task adds
`triage-archived` against the same shape rather than inventing a second
lifecycle.

## Steps

1. Write the failing tests first. In `tests/test_agentic_audit.py`, follow the
   existing cases' style: a fixture of 3 consecutive net-positive runs of one
   focus files exactly one finding naming that focus and its ratio; a mixed
   fixture files none; a second audit over the same fixture files nothing new
   (the dedup contract the module already documents).
2. Write `tests/test_janitor_triage.sh` over `mktemp -d` fixtures: a 15-day-old
   triage bead is listed, a 5-day-old one is skipped, `--dry-run` changes
   nothing observable (fixture sha256 unchanged), and a non-triage bead of any
   age is untouched.
3. Implement the audit class inside the existing counting and filing flow —
   the class computes from `drain-run` beads only, so a repo with none produces
   zero findings rather than an error.
4. Implement `--scope triage` in `bin/janitor`, extending the existing
   `valid_scope` list, its usage line, its summary counters, and the `--json`
   output. Add `TRIAGE_DECAY_DAYS` with default 14.
5. Register the new test in the test inventory.

## Acceptance

- [ ] `python3 -m pytest tests/test_agentic_audit.py -q` → passes, including
      the three new cases. **L2**
- [ ] `bash tests/test_janitor_triage.sh` → exits 0, reports 0 failures. **L2**
- [ ] `bin/janitor --scope triage --dry-run --json | jq -e '.scope == "triage"'`
      → true, and the 15-day fixture bead appears in the listing while the
      5-day one does not — asserted in the test. **L2**
- [ ] `bin/janitor --scope bogus; echo $?` → nonzero with the usage message
      naming `triage` among the valid scopes. **L2**
- [ ] `grep -c 'TRIAGE_DECAY_DAYS' bin/janitor` → ≥ 1 with default 14 (verified
      0 today, 2026-07-30). **L1**
- [ ] The dry-run no-op assertion passes: fixture sha256 unchanged after
      `--dry-run`. **L2**
- [ ] `bash scripts/check.sh` → `check.sh: green`. **L2**
