# Spec-completion review: one code-review-fix pass over a spec's cumulative diff

Status: open
Priority: P1

## Problem

Per-task code review already exists and works: /build's close-out invokes
`/code-review` at `low` effort on the task's diff, fixes
correctness/behavior findings inside the task's Touch immediately, and
re-runs acceptance (build SKILL.md, "Pre-commit review"); drain workers
inherit it via the build procedure. But its unit of review is one task's
diff — often under the 25-line skip gate, never more than one Touch
scope. Nobody reviews what a SPEC adds up to: cross-task seams
(task 02's summary sections consuming task 01's label semantics), the
union diff's duplication, or a defect visible only when sibling changes
land together. The 2026-07-11 runs merged 18 tasks across six specs with
zero spec-level review passes — every review that ran saw a slice.
Steven's ask (2026-07-11): "add a code review phase to our building /
draining, fixing high confidence review findings."

## Solution

A spec-completion review step in drain: when a spec reaches
nothing-left-to-dispatch with at least one DONE task (the lease-release
moment), drain computes the spec's cumulative product diff (merge-base of
the spec's first flip commit → current main, path-scoped to the union of
its tasks' Touch), skips it under the same NON-product/25-line gate build
uses, and otherwise dispatches ONE review-fix worker: run `/code-review`
equivalent review at high-confidence effort over that diff, apply ONLY
high-confidence correctness/behavior fixes inside the union Touch,
re-run the spec's acceptance-bearing gates, and return a verdict. Fixes
merge through the normal serial-merge machinery (a `task/`-style branch,
whitelist + Touch checks). Findings judged uncertain or out-of-scope
land as draft stubs via the existing materialize-discoveries path — never
silent, never auto-fixed.

Attended /build of a bare SPEC.md gets the same step at its close-out
(its diff IS the spec diff); no change to per-task review.

## Requirements

- R1 **Trigger and scope.** Drain runs the spec-completion review exactly
  once per spec per run, at the lease-release boundary, only when ≥1 task
  completed DONE this run. Diff = merge-base(first status-flip commit,
  main)..main restricted to the union of the spec's tasks' `Touch:` paths
  (product paths only). The build skip gate applies verbatim (NON-product
  classification + <25 product lines → record
  `spec review skipped: <reason>` in the spec's evidence/ and release the
  lease as today).
- R2 **Review-fix worker.** One worker (implementation-worker tier pin),
  worktree-isolated, awaited: reviews the diff for high-confidence
  correctness/behavior defects only (style excluded — /simplify territory;
  uncertain findings excluded), fixes them within the union Touch,
  re-runs the union of the spec's per-task gate commands, commits to
  `task/<slug>-spec-review`, returns the ≤2k verdict (findings found /
  fixed / discovered-out). Zero findings is a valid verdict and produces
  the evidence line, not silence.
- R3 **Merge + bookkeeping.** The fix branch merges through step 3's
  existing machinery (whitelist diff over tasks/, runtime Touch
  enforcement against the union Touch, serial merge, gates, push).
  Uncertain/out-of-scope findings materialize as draft stubs via the
  existing discoveries path. The exit checklist gains a line per spec:
  `spec review: N findings, M fixed, K stubbed` (or the skip reason).
- R4 **Attended parity.** /build on a bare SPEC.md (no tasks/) runs the
  same review at close-out using its existing pre-commit review
  machinery at the spec diff's scope — one sentence added to build
  SKILL.md's close-out citing this spec's trigger; no second review of
  task-file /build runs (their per-task pass already covers them).
- R5 **Wake economics respected.** The hub never reads the cumulative
  diff inline: it computes `git diff --stat` for the skip gate and passes
  the ref range to the worker. The review-fix worker's verdict is capped
  like every worker verdict.
- R6 **Mirror + plugin.** Content-equivalent addition to the antigravity
  drain workflow (and codex drain wrapper's worker-dispatch area if its
  summary embeds the lease-release sequence — check). Plugin version
  bumped in the closing task's own commit; `claude plugin validate .`
  passes; `bash evals/lint-ultra-gate.sh` green.

## Out of scope

- Changing the per-task pre-commit review (shape, effort, or skip gate).
- Reviewing docs-only specs (the skip gate handles them).
- Multi-round review loops (one pass, like the per-task review).
- Cross-SPEC review (a whole-repo audit is /code-review ultra's job).
- Blocking lease release on review failure — a failed review-fix merge
  reports and releases (the spec's tasks already passed their own gates).

## Acceptance criteria

- [ ] `grep -qi 'spec-completion review' .claude/skills/drain/SKILL.md`
  (phrase absent today — verified 2026-07-11) AND MANUAL: trigger is the
  lease-release boundary, once per spec per run, ≥1 DONE task, skip gate
  cited from build (R1)
- [ ] `grep -qi 'spec review skipped' .claude/skills/drain/SKILL.md`
  (phrase absent today) — the skip evidence line is specified (R1)
- [ ] MANUAL: worker contract in reference.md states high-confidence
  correctness/behavior only, union-Touch bound, gates re-run, ≤2k
  verdict, zero-findings explicit (R2)
- [ ] MANUAL: merge path reuses step 3 machinery; exit checklist line
  format present; uncertain findings route to draft stubs (R3)
- [ ] `grep -qi 'spec-completion review' .claude/skills/build/SKILL.md`
  (absent today) — one close-out sentence for bare-SPEC builds (R4)
- [ ] MANUAL: hub-side handling is --stat + ref range only (R5)
- [ ] `claude plugin validate .` passes; `bash evals/lint-ultra-gate.sh`
  green; plugin version line modified in the closing task's own commit;
  `grep -qi 'spec-completion review' antigravity/.agents/workflows/drain.md`
  (absent today) (R6)

## Open questions

(none)

## Parallelization

(/breakdown owns the map; likely: 01 = drain SKILL.md + reference.md
step (single writer), 02 = build SKILL.md sentence, 03 = closing
mirror/bump gate. 01 and 02 disjoint Touch. NOTE cross-spec contention:
specs/drain-forward-progress also edits drain SKILL.md/reference.md —
the two specs must not drain concurrently; sequence forward-progress
first or serialize via Touch overlap, and their closing tasks both bump
plugin.json relative to base.)
