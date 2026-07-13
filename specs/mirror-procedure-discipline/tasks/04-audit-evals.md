# Task 04: Audit evals's antigravity mirror for procedural divergence

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers. ## Progress / ## Deferred questions are drain-written sections. -->

Status: done
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

- [x] `bash tests/test_mirror_procedure_coverage.sh` → exit 0
- [x] `grep -c "checked: evals" tests/mirror-procedure-manifest.txt` → ≥1, OR a new manifest line referencing `evals` — evidence either way (grep → 1; also seeded a phrase line `.claude/skills/evals/SKILL.md|antigravity/.agents/workflows/evals.md|skill-authoring gap`)
- [x] `for t in tests/test_*.sh; do bash "$t" || echo "FAIL: $t"; done` → no FAIL lines (all suites green, 0 FAIL lines)
- [x] `bash evals/lint-ultra-gate.sh` → exit 0 (OK — all ultra mentions gated in 4 files)

## Progress

Full side-by-side read of `.claude/skills/evals/SKILL.md` (source) vs
`antigravity/.agents/workflows/evals.md` (only mirror surface — no
`.agents/skills/evals/` dir). Fixed two incidental drops:
1. Closing step "if a failure exposed a skill-authoring gap, distill the
   lesson" — restored (the distill workflow exists in the port, so the
   pointer resolves; phrased "apply the distill skill" per sibling
   build/autopilot convention).
2. Scaffold "model it on the /breakdown scenario" shape pointer — restored,
   adapted off the Claude-Code-only `reference.md` to the shared
   `evals/breakdown/` scenario dir that both runtimes can read.

Load-bearing diffs left as-is: run.sh→manual provision + Agent-Manager
launch, runner env vars (EVAL_DIR / timeout 900 / MAX_TURNS / EVALS_ROOT)
dropped (no runner), allowed-tools.txt ignored, added bash-3.2 caveat.

Decisions:
- teardown.sh omission re-confirmed load-bearing (not reopened). `agy -p` is
  live-tested UNSAFE for isolated/unattended use (`runtimes/antigravity.md`),
  so evals on Antigravity runs manually via Agent Manager with no automated
  runner to invoke teardown; the responsibility shifts to the human
  operator. Left as-is per the task's "confirm the finding still holds"
  scope. Reversible default taken: did NOT add a manual-teardown step,
  since doing so would re-open a pre-adjudicated load-bearing classification.

Discovered (out of scope, follow-up for orchestrator/human): the manual
Antigravity flow (steps 2–4) never names teardown.sh at all — an operator
porting an eval that seeds external live-service state gets no cue to run
it. Worth a one-line "operator runs teardown.sh after the session" note in
a future pass, if the maintainer agrees it belongs in the manual flow.

## Discovered

- The manual Antigravity evals flow never names `teardown.sh` — an operator
  running an eval that seeds external live-service state gets no cue to
  clean it up. See `specs/mirror-procedure-discipline/tasks/16-manual-evals-teardown-cue.md`.
