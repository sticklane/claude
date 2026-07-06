# Task 01: Replace drain's group barrier with a rolling-window scheduler

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Priority values run P0 (highest) through P3; the header is optional — absent means P2. -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers, in every task file — and ## Progress / ## Deferred questions are drain-written sections (single writer, main checkout): workers report that content, never write it. -->

Status: done
Depends on: none
Priority: P0
Budget: 30 turns
Spec: ../SPEC.md (requirements R1, R2, R3, R4, R8, R8a, R9)
Touch: .claude/skills/drain/SKILL.md, .claude/skills/drain/reference.md

## Goal

`.claude/skills/drain/SKILL.md`'s "## 2. Dispatch" section no longer
describes the strict group barrier (flip-all-in-one-commit, launch-all,
wait-for-all). It describes a rolling window of W concurrent workers:
admission (R1), top-up on each verdict rather than on a wave boundary
(R2), a serial merge queue with mechanical rebase-in-scratch-worktree
recovery (R3), and runtime Touch enforcement at merge (R4). `reference.md`
carries the R8 drain-down/baton interaction, the R8a tournament-in-an-
emptied-window rule, and the R9 termination properties (no hold-and-wait
cycle, every run terminates, the pending set shrinks or the run ends) in
whatever section already documents baton pass / tournament / zombie
escalation. The existing owner-lease/CAS protocol (specs/
multi-session-coordination) is untouched — same literal strings, same
section — because this task changes *when* drain dispatches, not *how*
it flips a `Status:` line.

## Touch

In scope: the "**Group throughput mode**" paragraph and its enclosing
"## 2. Dispatch (one worker, or one independent group)" heading in
SKILL.md; reference.md's "## Tournament", "## Baton pass (self-relaunch)",
and "## Stale-lock liveness check" / zombie-escalation sections (extend,
don't restructure, unless the rolling-window semantics require it).

Out of scope — do not touch, only read: the "**The flip is
compare-and-swap.**" subsection and everything under "## 1. Inventory",
"## 3. Collect the verdict", "## 3a. Baton pass" outside the R8 drain-down
addition, and "## Owner lease" / "Run-token" / "DRAIN-OWNER" text in
reference.md. Those implement the write protocol from
specs/multi-session-coordination and must survive this rewrite with their
exact literal strings intact (see Acceptance) — this task adds scheduling
prose around them, never edits their sentences.

## Steps

1. Read `.claude/skills/drain/SKILL.md` sections "## 2. Dispatch" and
   "## 3a. Baton pass", and `reference.md`'s "## Tournament",
   "## Baton pass (self-relaunch)", and "## Stale-lock liveness check"
   sections in full before editing anything.
2. In SKILL.md, replace the "**Group throughput mode**" paragraph with
   rolling-window text carrying R1's admission predicate verbatim in
   substance: window size W (default 1; `Parallel-window: N` header;
   explicit user request overrides; hard cap 5); the claim set (Touch of
   every committed `Status: in-progress` task, zombie or not); the
   co-admissibility rule (two tasks may be in flight together iff a
   single `Group:` line in the spec's Parallelization section names
   both; a task on no `Group:` line runs solo, and nothing else runs
   while it does). Document the `Group:` line grammar itself here (one
   line per group, `- Group: NN, NN[, NN...]`, two-digit task numbers) —
   this SPEC's own Parallelization section (specs/drain-rolling-window/
   SPEC.md) pins the exact format; cite it rather than re-deriving it,
   and keep the two documents' wording consistent since task 02 emits
   the producing side of the same grammar.
3. Add R2's top-up rule: after each verdict is collected and (for DONE)
   merged + pushed, drain re-computes admission and refills the window —
   status flips stay one committed flip per task, no all-members-one-
   commit.
4. Add R3's serial merge queue: one merge at a time, landing order; on a
   conflict from a sibling merging after this branch's base was cut,
   one `git rebase main` attempted in a throwaway scratch worktree cut
   for the rebase (reusing the worker's own worktree if it survived);
   never `git checkout` a task branch in the shared checkout; a clean
   rebase proceeds to normal DONE bookkeeping, conflicts route to the
   existing cross-task interference rule.
5. Add R4: extend the merge-time whitelist diff so the branch's changed
   paths must be a subset of the task's `Touch:` list plus its own task
   file plus the spec's `evidence/` dir; a violation is a merge failure.
6. In reference.md, extend the baton-pass section with R8: a baton
   trigger enters drain-down (stop admitting, wait out every in-flight
   worker, record+commit each, then write the baton only at window-empty
   quiescence); the verdict counter counts recorded verdicts regardless
   of window size.
7. Extend the Tournament section with R8a: a qualifying task holds all
   new admissions, waits for every in-flight sibling to land, then
   dispatches the tournament's three workers into the otherwise-empty
   window (exactly 3 live workers regardless of W); admissions resume
   after verdict routing completes.
8. Extend the zombie-escalation text with R9.2: a zombie-escalated task
   releases its window slot but its Touch claim persists (its committed
   `Status:` stays `in-progress`, so R1's claim set already covers it) —
   overlapping tasks are refused admission and reported "blocked by
   suspected zombie `<task>`", not silently starved.
9. Add R9.3's termination check: when admission is ACTIVE (never during
   an R8 drain-down or R8a tournament hold) and the admission function,
   actually evaluated, returns empty, drain must detect an unsatisfiable
   remainder (a `Depends on:` cycle, or every pending task transitively
   depending on tasks that cannot complete this run) and route to the
   batch interview / final report instead of waiting forever.
10. Re-read the untouched sections you were told not to edit and confirm
    every literal string in Acceptance below is still present, unchanged.

## Acceptance

- [x] `grep -c 'Parallel-window' .claude/skills/drain/SKILL.md` → ≥ 1
- [x] `grep -c '^- Group:\|Group:' .claude/skills/drain/SKILL.md` → ≥ 1
      (drain documents the consuming side of the grammar pinned in
      specs/drain-rolling-window/SPEC.md's Parallelization section)
- [x] `grep -n 'Group throughput mode' .claude/skills/drain/SKILL.md` →
      no output (the strict-barrier heading is gone)
- [x] `grep -c "DRAIN-OWNER" .claude/skills/drain/SKILL.md` → ≥ 2 (claim +
      release, unchanged from specs/multi-session-coordination)
- [x] `grep -n "compare-and-swap\|exact-match" .claude/skills/drain/SKILL.md`
      → non-empty
- [x] `grep -c "pull --rebase" .claude/skills/drain/SKILL.md` → ≥ 1
- [x] `grep -c "Run-token" .claude/skills/drain/reference.md` → ≥ 2
- [x] `grep -ci "tournament" .claude/skills/drain/reference.md` → ≥ 1 and
      `grep -ci "emptied\|empty window\|window-empty" .claude/skills/drain/reference.md`
      → ≥ 1 (R8a's emptied-window rule is present)
- [x] `grep -ci "zombie" .claude/skills/drain/reference.md` → ≥ 1 and
      `grep -ci "blocked by suspected zombie" .claude/skills/drain/SKILL.md .claude/skills/drain/reference.md`
      → ≥ 1
- [x] R2 top-up is stated, not just admission: `grep -ci "top.up\|re-computes admission\|refills the window" .claude/skills/drain/SKILL.md`
      → ≥ 1
- [x] R3's rebase recovery is stated: `grep -ci "scratch worktree\|throwaway.*worktree" .claude/skills/drain/SKILL.md`
      → ≥ 1
- [x] R4's merge-time Touch enforcement is stated (this is the spec's
      headline safety requirement — closing the plan-time-only
      enforcement gap — and must be verifiable here, not only inferred
      from good-behavior fixtures elsewhere in this spec):
      `grep -ci "subset of the task" .claude/skills/drain/SKILL.md` → ≥ 1,
      and the text names the consequence: `grep -ci "merge failure\|slot.machine" .claude/skills/drain/SKILL.md`
      → ≥ 1

Evidence: all 12 criteria verified green by the verifier agent (fresh eyes,
base 5e8fc23) — full per-criterion command output in
../evidence/01-drain-rolling-window-scheduler.md. Verdict PASS, no scope
creep (only the two drain skill files + this task file changed).

## Discovered

- Stale cross-reference in `.claude/skills/drain/SKILL.md`'s "## 3. Collect the verdict" push-guard parenthetical (line 249): still reads "drain's own group mode follows it" — the group mode it names no longer exists after this task's rewrite; should read "drain's own rolling-window merges." See specs/drain-rolling-window/tasks/07-fix-stale-group-mode-reference.md.
