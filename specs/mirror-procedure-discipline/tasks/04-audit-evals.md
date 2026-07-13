# Task 04: Audit evals's antigravity mirror for procedural divergence

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers. ## Progress / ## Deferred questions are drain-written sections. -->

Status: in-progress
Depends on: 01
Priority: P2
Budget: 8 turns
Spec: ../SPEC.md (requirement R5)
Touch: antigravity/.agents/workflows/evals.md, tests/mirror-procedure-manifest.txt

## Goal

`evals`'s Antigravity mirror (`antigravity/.agents/workflows/evals.md` —
there is no `antigravity/.agents/skills/evals/` directory; this is the only
mirror surface) is read side-by-side against its source
(`.claude/skills/evals/SKILL.md`) and reconciled per
`.claude/rules/mirror-procedure-discipline.md`'s load-bearing-vs-incidental
classification (read that rule first — task 01 must be done before this one
starts).

Note: a prior scout pass this session already checked `evals` and found its
divergence (Antigravity's scaffold step omits `teardown.sh`) is
load-bearing, not incidental — justified by `agy -p` (the real headless
Antigravity CLI) being live-tested unsafe for isolated/unattended use
(`runtimes/antigravity.md`), so `evals` on Antigravity only runs manually,
shifting teardown responsibility to the human operator. This task's job is
to confirm that finding still holds on a fresh read (things may have
changed) and check the REST of the procedure for anything the prior pass
didn't specifically look at — the prior check was scoped to the
teardown.sh question only, not a full side-by-side read.

## Touch

Only the two files listed in the header. Do not touch any other skill's
mirror files, `.claude/skills/evals/` (the source — reconcile the mirror TO
it, never edit the source), or the rule/gate files from task 01.

## Steps

1. Read `.claude/rules/mirror-procedure-discipline.md` (task 01's output)
   for the divergence classification.
2. Read `.claude/skills/evals/SKILL.md` in full as the source of truth.
3. Read `antigravity/.agents/workflows/evals.md` in full.
4. Compare procedure, not prose, for the WHOLE file (not just the
   teardown.sh question already checked): confirm the manual-launch
   adaptation is consistently applied, and look for any other incidental
   gap (missing step, dropped nuance, swapped order) beyond what's already
   load-bearing per the note above.
5. Fix any incidental divergence found — small, targeted edits.
6. Append a manifest line if phrase-expressible, or a
   `# checked: evals — <summary>` comment line to
   `tests/mirror-procedure-manifest.txt` (this must be written regardless
   of outcome, since the teardown.sh finding alone doesn't count as a full
   audit per this task's Goal).
7. Run the acceptance commands yourself before marking done.

## Acceptance

- [ ] `bash tests/test_mirror_procedure_coverage.sh` → exit 0
- [ ] `grep -c "checked: evals" tests/mirror-procedure-manifest.txt` → ≥1, OR a new manifest line referencing `evals` — evidence either way
- [ ] `for t in tests/test_*.sh; do bash "$t" || echo "FAIL: $t"; done` → no FAIL lines
- [ ] `bash evals/lint-ultra-gate.sh` → exit 0
