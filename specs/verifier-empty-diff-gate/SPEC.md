# Verifier empty-diff pre-check before spending acceptance-command budget

Status: open
Priority: P2
Breakdown-ready: true

## Problem

Today's Workflow-tool (ultracode) runs, sampled across this machine's active
repos, gave a concrete instance of a failure mode the `verifier` agent
(`.claude/agents/verifier.md`) has no defense against: a dispatched
implementation worker self-reported a task as merged, but the merged
branch's working tree was byte-for-byte identical to its base — no change
had actually landed. The `verifier` agent still ran its full Process
(steps 1–7: read criteria, EXERCISE every criterion, run project gates,
check for scope creep and overfitting) against that no-op diff, spending
tool calls and turns discovering, criterion by criterion, that nothing had
changed — a fact one mechanical `git diff` would have surfaced for free
before any of that ran. (The acceptance commands themselves are explicitly
exempted from the verifier's ~20-call ceiling per the file's own text — the
waste here is tool calls, tokens, and turns across steps 2–7, not ceiling
consumption.)

`verifier.md`'s Process (steps 1–7) has no step that checks, before doing
any of that work, whether the implementation actually touched anything.
Both `/build` (SKILL.md step 3.3, "Verify with fresh eyes") and `/drain`
(reference.md's Worker prompt / step 3, "Collect the verdict") dispatch
this same `verifier` agent, so a fix here benefits both callers uniformly
without touching either skill — but the check has to handle real inputs
correctly, not just the happy path. Three concrete traps a naive `git
diff <base>` hits, all reachable in normal use:

1. **Untracked new files.** `/build` verifies before commit (verifier.md's
   own step-2 restore-caution note confirms this). A task whose deliverable
   is a *new* file leaves it untracked at verify time, and `git diff
   <base> -- <path>` does not show untracked files — a plain diff would
   false-FAIL a genuinely-done task. `/build`'s own pre-commit review gate
   already hit this and solved it by staging first: `git add -A && git
   diff <step0-base> --numstat` (build/SKILL.md, "Pre-commit review").
2. **No Touch list to restrict to.** A bare `specs/<slug>/SPEC.md` (which
   `/build` verifies directly per its step 3.3) carries no `Touch:` header,
   and `Touch:` is optional on older task files. "Restrict the diff to the
   Touch-list paths" is undefined when that list is empty — reading it as
   "no pathspec" diffs everything (over-broad), reading it as "diff
   nothing" always returns empty (guaranteed false FAIL).
3. **Base resolution already has a defined fallback.** Step 6's append-only
   check does not treat "no base was passed" as a dead end — it resolves
   the base as "the caller passed one, **or**, in a drain/tournament
   worktree, the worktree's merge-base with the default branch." A new
   check that invents its own separate "missing base" branch would give the
   file two different, possibly conflicting, ways to find a base commit.

## Solution

Add a mechanical, zero-agent-judgment pre-check as a new step 0 in
`verifier.md`'s Process, run before step 1 ("read the acceptance
criteria"):

- Resolve the base exactly as step 6 already does (passed base, or
  worktree merge-base with the default branch) — do not invent a second
  resolution path.
- Stage everything first (`git add -A`, mirroring `/build`'s own
  pre-commit review gate) so untracked new files are visible, then diff
  against the resolved base.
- If the task file carries a `Touch:` list, restrict the diff to those
  paths; if it carries none (a bare SPEC.md, or a pre-`Touch:` task file),
  do not restrict — diff unrestricted against the base, matching how the
  file is verified today without this check.
- If that diff is empty, return `FAIL` immediately with the single finding
  "no changes made — working tree matches base," explicitly stating that
  steps 1–7 were skipped and no acceptance command ran. If no base can be
  resolved at all (step 6's own fallback also comes up empty), or the diff
  is non-empty, proceed to step 1 exactly as today.

**Depth ceiling (acceptance-criteria scope):** this spec edits a prompt
file, not executable code — the acceptance criteria below are L0
(text-presence / phrase-anchored), the same ceiling this repo's other
agent-prompt specs (e.g. `specs/agentic-prose-tells`) accept for prose-file
edits. Confirming the verifier *actually* skips steps 1–7 on a live
no-op diff, before running any acceptance command, requires a real model
session and is out of scope for this spec's runnable gate; a human or a
follow-up eval run confirms the live behavior post-merge.

## Requirements

- R1: `.claude/agents/verifier.md`'s Process gains a new step 0, run
  before the existing step 1, implementing exactly the four bullets in
  Solution above (base resolution reuses step 6's; stage before diffing;
  Touch-list restriction only when a Touch list exists; empty diff →
  immediate `FAIL` with the stated finding, skipping steps 1–7 entirely
  and running no acceptance command).
- R2: The Output format section's verdict-line description is unchanged
  (still `PASS`/`FAIL`/`INCOMPLETE`) — the new step only ever produces
  `FAIL`, never a new verdict value, so `/build` and `/drain`'s existing
  verdict-routing logic (fix-and-reverify, merge-failure relaunch, slot
  machine) needs no change to handle it. The Output format section's
  mandatory per-requirement criteria-adequacy line (step 7's output
  contract) is explicitly exempted for a step-0 empty-diff FAIL: that
  verdict emits only the verdict line and the single "no changes made"
  finding, never a per-requirement adequacy line, since step 0 never
  reached step 1 to read the requirements it would apply to.

## Out of scope

- Changing `/build` or `/drain` to run their own pre-check before spawning
  the verifier (a caller-side check would save the agent-spawn cost too,
  but doubles the file surface for a first pass; if the verifier-side
  check proves valuable, a caller-side mirror is a natural follow-up, not
  bundled here).
- Any change to the append-only task-file diff check (step 6) or the
  criteria-adequacy ladder (step 7) — both are unchanged, just skipped
  when the new step 0 already returned FAIL. Step 0 reuses step 6's base
  resolution by reference; it does not restate or duplicate it.
- Live behavioral confirmation that the skip actually fires — deferred
  per the Depth ceiling note above.

## Acceptance criteria

- [ ] `grep -qi 'no changes made' .claude/agents/verifier.md`
- [ ] `grep -qi 'empty diff\|diff is empty' .claude/agents/verifier.md`
- [ ] `grep -qi 'git add -A\|stage.*untracked\|untracked' .claude/agents/verifier.md` — the untracked-file trap is explicitly handled, not just the happy-path diff
- [ ] `grep -qiE 'skip(s|ping)? (steps? 1|all remaining steps)' .claude/agents/verifier.md` — the skip scope is stated as 1–7 (or "all remaining steps"), not the ambiguous "2–7" this spec's first draft used
- [ ] `tr '\n' ' ' < .claude/agents/verifier.md | grep -qiE 'adequacy[^.]*exempt|exempt[^.]*adequacy'` — the step-0 FAIL's exemption from the mandatory per-requirement criteria-adequacy line is stated in the same sentence as "adequacy," not left to clash silently with step 7's output contract
- [ ] `grep -qiE 'no (touch|touch-list|touch list)|without.*restrict' .claude/agents/verifier.md` — the no-Touch-list case is addressed, not left undefined
- [ ] MANUAL: the new step 0 is positioned before step 1 in the file's line
  order (`grep -n` both markers and confirm step 0's line number is lower)
- [ ] MANUAL: step 0's base-resolution language points at step 6's
  resolution (same fallback: passed base, or worktree merge-base with
  default branch) rather than defining an independent "missing base"
  branch
- [ ] MANUAL: the file's Output format section still lists exactly three
  verdict values (`PASS`/`FAIL`/`INCOMPLETE`) — unchanged by this spec

## Parallelization

Single requirement, single file, single task — no parallelization needed.
