# Task 08: bin/spec-gate — score a spec's acceptance surface

<!-- Registration fields (Depends on, Budget, Touch, Rigor) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. Status and Priority are frozen authoring-time display only: bd owns their live values. -->

Status: pending
Depends on: 07
Priority: P1
Budget: 40 turns
Spec: ../SPEC.md (requirements EP12, decision D2)
Touch: bin/spec-gate, tests/test_spec_gate.sh, tests/fixtures/spec-gate, tests/inventory/drain-economy.json, specs/toolkit-core-simplification/surface-inventory/drain-economy.json

## Goal

`bin/spec-gate <slug> [--tier cheap|all]` parses a spec's acceptance block
under task 07's grammar, runs each selected criterion, writes
`specs/<slug>/acceptance-status.json` as records of `{id, tier, pass|fail|skip,
ts}`, and exits 0 iff every executed criterion passed. The JSON is committed, so
a spec's acceptance trend is a `git log` away. This is the script that makes
proximity a measured number rather than a task count.

## Touch

The gate runs criteria; it never edits the spec, never files a bead, and never
decides what to do about a failure — drain's ceremony (task 12) and the report
(task 05) consume its output. It must NOT reach into `bin/spec-status` (task
09), which derives a different set of numbers from bd history.

Criteria are arbitrary shell commands out of a repository file, so the command
policy matters: apply the same policy that gates `Unblock: run:` execution in
task 02 rather than inventing a second one, and refuse — recording `skip` with
a reason — rather than executing a rejected command.

## Steps

1. Write the failing test first: `tests/test_spec_gate.sh` over fixture specs
   under `tests/fixtures/spec-gate/`, each with its own acceptance block.
   Assert on the JSON records, not on stdout prose.
2. Cover the core cases: one passing plus one failing criterion writes both a
   `pass` and a `fail` record and exits 1; after the failing command is fixed
   the same invocation exits 0; `--tier cheap` executes only cheap criteria and
   records the expensive ones as `skip`; a block that does not parse exits
   nonzero with a message naming the grammar, and writes no partial status file.
3. Cover the policy case: a criterion whose command the policy rejects records
   `skip` with the reason and is never executed — asserted by sentinel absence,
   the technique `tests/test_human_blockers.sh` uses.
4. Implement `bin/spec-gate`, matching the existing `bin/` scripts' language and
   conventions. Each record carries its id, tier, verdict, and timestamp; the
   file is written atomically so an interrupted run leaves the previous status
   intact.
5. Run every criterion with the repository root as cwd and a bounded timeout,
   so one hanging criterion cannot wedge a drain pass.
6. Register the new script, fixtures, and test in the surface and test
   inventories.

## Acceptance

- [ ] `bash tests/test_spec_gate.sh` → exits 0, reports 0 failures. **L2**
- [ ] Mixed fixture: `bin/spec-gate <fixture> ; echo $?` → 1, and
      `jq -r '[.[]|.status]|sort|join(",")' specs/<fixture>/acceptance-status.json`
      → `fail,pass`; after the fixture's failing command is repaired the same
      invocation exits 0 and the same query returns `pass,pass`. **L2**
- [ ] `bin/spec-gate <fixture> --tier cheap && jq -e '[.[]|select(.tier=="expensive" and .status=="skip")]|length>0' specs/<fixture>/acceptance-status.json`
      → true, proving tier filtering records rather than silently drops. **L2**
- [ ] Non-parsing fixture: exit is nonzero, the message names the grammar, and
      `test -e specs/<fixture>/acceptance-status.json` reflects the pre-run
      state — asserted in the test. **L2**
- [ ] The policy fixture's sentinel file is absent after the run — asserted in
      the test. **L2**
- [ ] `python3 scripts/inventory-core-surface.py --root . --check specs/toolkit-core-simplification/BASELINE.json 2>&1 | grep -c 'unclassified\|drift'` → 0. **L2**
- [ ] `bash scripts/check.sh` → `check.sh: green`. **L2**
