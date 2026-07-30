# Task 12: the feature completion ceremony

<!-- Registration fields (Depends on, Budget, Touch, Rigor) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. Status and Priority are frozen authoring-time display only: bd owns their live values. -->

Status: pending
Depends on: 04, 08
Priority: P1
Budget: 30 turns
Spec: ../SPEC.md (requirement EP20)
Touch: .claude/skills/drain/SKILL.md, .claude/skills/drain/reference.md, evals/drain/06-ceremony/setup.sh, evals/drain/06-ceremony/prompt.txt, evals/drain/06-ceremony/assert.sh, evals/drain/06-ceremony/allowed-tools.txt, evals/drain/06-ceremony/skill-deps.txt, evals/drain/06-ceremony/timeout-seconds.txt, tests/inventory/drain-economy.json

## Goal

Finishing a feature becomes a mechanical ceremony rather than a judgment call.
When the focus frontier is empty with no open blocked or deferred items in
scope, drain runs `bin/spec-gate <slug> --tier all`. Green: it dispatches the
spec-completion review, files the evidence, appends the historical entry to
`specs/QUEUE.md`, removes the slug from NOW.md, sets the spec `Status: done`,
and closes the run bead with the ceremony recorded. Red: each failing criterion
files a blocking child and the run continues — the gate's failures *are* the
new frontier.

## Touch

This is the one place NOW.md is edited by a machine, and only to remove a
completed slug — every other NOW.md edit stays human-only, and this task must
state that boundary where it writes the removal step. It appends to
`specs/QUEUE.md`'s history and changes nothing else there.

It must NOT alter `bin/spec-gate` (task 08) or the report's sections (task 05);
it consumes both. The spec-completion review is existing practice — dispatch it
as it already works rather than defining a new review.

## Steps

1. Add the ceremony to `.claude/skills/drain/SKILL.md` at the point the loop
   detects an empty focus frontier: the emptiness precondition (no open
   blocked or deferred items in scope), the `--tier all` gate run, and the two
   branches.
2. Write the green branch as an ordered checklist so a worker cannot land half
   of it: review dispatched, evidence filed, QUEUE.md history appended, slug
   removed from NOW.md, spec `Status: done`, run bead closed with the ceremony
   recorded.
3. Write the red branch: one blocking child per failing criterion, each citing
   its criterion id from `acceptance-status.json`, the run bead left open, and
   the run continuing on the new frontier.
4. State the NOW.md write boundary explicitly: the completion removal is the
   only machine edit to that file.
5. Put the checklist's long form in `reference.md` if SKILL.md would exceed its
   size budget; the branch points themselves stay in SKILL.md.
6. Author `evals/drain/06-ceremony/` with both fixtures: a green-gate spec that
   completes the full checklist, and a red-gate spec that files one blocking
   child per failing criterion and keeps the run open.

## Acceptance

- [ ] `awk '/^## Archive on completion/{f=1} f&&/^## The batch interview/{exit} f' .claude/skills/drain/SKILL.md | grep -c 'spec-gate'` → ≥ 1
      (verified 0 in the whole file today, 2026-07-30; anchored to the
      completion section rather than a file-wide literal). **L0** — Depth
      ceiling: skill prose is not executable; the behavioral complement is the
      `evals/drain/06-ceremony` scenario below.
- [ ] `grep -c 'NOW.md' .claude/skills/drain/SKILL.md` → ≥ 3, with the removal
      step and the human-only boundary both present — asserted by reading the
      matched lines. **L0** — Depth ceiling: as above.
- [ ] `wc -l < .claude/skills/drain/SKILL.md` → < 500. **L1**
- [ ] `ls evals/drain/06-ceremony/ | wc -l` → 6, and
      `grep -c 'acceptance-status.json' evals/drain/06-ceremony/assert.sh` → ≥ 1. **L1**
- [ ] `bash evals/run.sh drain` → both ceremony fixtures pass. **L3** —
      `manual-pending`: paid headless session; a human runs it and records the
      result (`docs/memory/unattended-worker-tool-limits.md`).
- [ ] `bash scripts/check.sh` → `check.sh: green`. **L2**
