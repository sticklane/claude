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

- R1 **Trigger, scope, idempotency.** Drain runs the spec-completion
  review at the lease-release boundary, only when ≥1 task completed DONE
  this run. Ordering is pinned: run review → commit the evidence line →
  release the lease; the committed evidence file
  (`specs/<slug>/evidence/spec-review.md`, carrying either
  `spec review:` or `spec review skipped:`) is the idempotency token — a
  generation (or resumed run) finding it already committed SKIPS the
  review, which is what makes "once per spec per run" hold across baton
  generations without a new baton line. Diff base: the status-flip
  commit message becomes a PINNED contract (drop the current "e.g."):
  `drain: <spec-slug> task NN in-progress`; recovery command =
  `git log --reverse --format=%H --grep='^drain: <slug> task .* in-progress' -- 'specs/<slug>/tasks/'`,
  first match; a spec with no such commit (drained before this ships)
  skips with that stated reason. Diff =
  merge-base(<that commit>, main)..main restricted to the union of the
  spec's tasks' `Touch:` paths (product paths only). The build skip gate
  applies verbatim (NON-product classification + <25 product lines →
  the `spec review skipped: <reason>` evidence line, then release as
  today); the hub computes it from `git diff --numstat` (names + counts
  only — matching build's parse; never file contents).
- R2 **Review-fix worker.** One worker (implementation-worker tier pin),
  worktree-isolated, awaited: reviews the diff — via `/code-review` at
  the `low` effort tier where invocable (matching build's per-task pass;
  build SKILL.md:~143), else the fallback subagent shape build already
  defines — keeping ONLY high-confidence correctness/behavior findings
  ("high-confidence" is the FINDING FILTER, not an effort tier; style
  excluded — /simplify territory; uncertain findings excluded), fixes
  them within the union Touch, re-runs the union of the spec's per-task
  gate commands, commits to `task/<slug>-spec-review`, returns the ≤2k
  verdict (findings found / fixed / discovered-out). Zero findings is a
  valid verdict and produces the evidence line, not silence.
- R3 **Merge + bookkeeping (task-file coupling nulled).** The fix branch
  merges through step 3's serial merge + gates + push, with the
  task-file-coupled parts explicitly ADAPTED: the review branch has NO
  task file, so the runtime-Touch allowed set is the union Touch plus
  the spec's `evidence/` dir ONLY (the "task's own file" term is null),
  the append-only whitelist diff over `'*/tasks/*.md'` must be EMPTY
  (any tasks/ change on this branch is a merge failure), and NONE of the
  DONE bookkeeping runs (no Status flip, no checkbox ticks, no plan-block
  handling — there is no task). Uncertain/out-of-scope findings
  materialize as draft stubs via the existing discoveries path. The exit
  checklist gains a line per spec:
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
