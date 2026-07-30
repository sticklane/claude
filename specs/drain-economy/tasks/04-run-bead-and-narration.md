# Task 04: the run bead and loop narration

<!-- Registration fields (Depends on, Budget, Touch, Rigor) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. Status and Priority are frozen authoring-time display only: bd owns their live values. -->

Status: pending
Depends on: 03
Priority: P1
Budget: 30 turns
Spec: ../SPEC.md (requirements EP5, EP7, decision D4)
Touch: .claude/skills/drain/SKILL.md, .claude/skills/drain/reference.md, tests/test_drain_run_bead.sh, tests/inventory/drain-economy-04.json, evals/drain/05-run-bead/setup.sh, evals/drain/05-run-bead/prompt.txt, evals/drain/05-run-bead/assert.sh, evals/drain/05-run-bead/allowed-tools.txt, evals/drain/05-run-bead/skill-deps.txt, evals/drain/05-run-bead/timeout-seconds.txt

## Goal

Every drain run has an accounting identity and a visible pulse. At launch drain
opens a run bead titled `drain <focus-or-all> <ISO-date>`, labelled
`drain-run`, whose body carries the NOW.md snapshot, the launch argument, and
the session id; at exit it closes that bead with the computed report. An
interrupted run leaves the bead open, and the next drain of the same focus
reuses an open one younger than 24h. After every collected verdict the run
emits one line to both the session and the run log, plus a line at every focus
transition and re-focus.

## Touch

This task defines the bead's shape and the run log's line format — the two
inputs `bin/drain-report` (task 05) and `bin/drain-watch` (task 06) consume, so
their formats must be stated precisely enough to parse. It writes no `bin/`
script itself. The run bead is a *convention* only (D4): `agentic dispatch/run/watch`
stays parked under its existing Unblock condition and is not unparked here.

The narration line's grammar is fixed by the spec:
`closed <id> (<i>/<n> in focus) · opened <b>b+<t>t · in-flight: <id> <role> attempt-<a>`.
Task 02 already wrote the focus-transition line; this task states where the run
log lives and that the transition line is written to it too.

This task also owns the **spillover-event record**, deliberately: task 02
writes the spillover branch and its narration, but the bead that a spillover
event is recorded on does not exist until this task creates it. Adding the
record here — rather than leaving task 02 to improvise a surface — is what
keeps `bin/drain-report`'s "spillover events with reasons" section (EP6) from
rendering an empty list against a mechanism that fired.

## Steps

1. Write the failing test first: `tests/test_drain_run_bead.sh` over
   `mktemp -d` fixtures, asserting the parseable contract — a fixture run log
   containing the narration lines parses into per-closure records with the
   documented fields, a malformed line is rejected rather than silently
   skipped, and the reuse window boundary (a 23h-old open `drain-run` bead is
   reused, a 25h-old one is not) resolves as documented. Assert on structure,
   not on exact prose.
2. Document the run-log location and its line grammar in
   `.claude/skills/drain/reference.md`, in a section a later script can cite:
   the closure line, the focus-transition line, and the re-focus line, each
   with its field order and separator.
3. Edit `.claude/skills/drain/SKILL.md`'s launch and exit steps: open the bead
   with the stated title, label, and body fields; close it at exit with the
   report; leave it open on interruption; reuse an open same-focus bead younger
   than 24h rather than opening a second.
4. Edit the loop step that collects verdicts so one narration line is emitted
   per collected verdict, to both the session and the run log.
5. Add the spillover-event record to task 02's blocked-frontier branch: each
   spillover appends an event to the run bead carrying the abandoned focus, the
   destination, and the reason (the `ask:` count, or the policy reason code
   that demoted a `run:`). Extend `tests/test_drain_run_bead.sh` to assert the
   recorded event's fields parse — this is the input EP6's report reads.
6. Keep SKILL.md under its size budget — the grammar detail belongs in
   `reference.md`.
7. Author `evals/drain/05-run-bead/`: a fixture run whose assertions check that
   a `drain-run` bead exists naming the focus, that it closes, and that the run
   log holds one closure line per closed issue.

## Acceptance

- [ ] `bash tests/test_drain_run_bead.sh` → exits 0, reports 0 failures. **L2**
- [ ] `grep -c 'drain-run' .claude/skills/drain/SKILL.md` → ≥ 1 (verified 0 in
      the whole file today, 2026-07-30). **L0** — Depth ceiling: skill prose is
      not executable; the behavioral complement is the
      `evals/drain/05-run-bead` scenario below.
- [ ] `awk '/^## /{s=$0} /in focus/{print s}' .claude/skills/drain/reference.md | head -1 | grep -c .` → 1,
      proving the narration grammar landed inside a named reference section
      rather than loose in the file (the literal `in focus` verified 0 in both
      drain files today, 2026-07-30). **L0** — Depth ceiling: as above.
- [ ] The spillover-event assertion passes: a fixture spillover records an
      event whose focus, destination, and reason fields parse — asserted in
      `tests/test_drain_run_bead.sh`. **L2**
- [ ] `wc -l < .claude/skills/drain/SKILL.md` → < 500. **L1**
- [ ] `ls evals/drain/05-run-bead/ | wc -l` → 6, and
      `grep -c 'drain-run' evals/drain/05-run-bead/assert.sh` → ≥ 1. **L1**
- [ ] `bash evals/run.sh drain` → the new scenario passes. **L3** —
      `manual-pending`: paid headless session; a human runs it and records the
      result (`docs/memory/unattended-worker-tool-limits.md`).
- [ ] `bash scripts/check.sh` → `check.sh: green`. **L2**
