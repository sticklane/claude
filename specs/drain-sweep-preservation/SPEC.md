# Drain sweep preservation: don't destroy uncommitted work, and halt on environment kills

> **Provenance.** 2026-07-05, /Users/sjaconette/hub: the weekly API limit killed a
> drain worker AND its verifier mid-verdict. The worker had the complete, probably-green
> implementation sitting UNCOMMITTED in its worktree — its task branch had ZERO commits
> beyond the dispatch base, because workers commit at close-out. Drain's standard sweep
> ("Force-remove each worktree FIRST, then rename the branch to rescue/…") would have
> silently destroyed finished work and preserved an empty branch. The orchestrator
> improvised the right behavior (WIP snapshot commit inside the worktree, then sweep);
> this spec makes that behavior — and the run-level halt a global API limit demands —
> part of the skill text.

## Problem

Two gaps in `.claude/skills/drain/`:

1. **The sweep can destroy the only copy of finished work.** reference.md's
   rescue procedure (Status field semantics, ~lines 52–65) force-removes each
   worktree before renaming branches, and the "Residual risk" note explicitly
   treats worktree writes as discardable. That is correct for task failures
   (slot-machine doctrine) but wrong in the common crash case: a worker that
   dies between finishing implementation and its close-out commit leaves a
   dirty worktree and an empty branch. The rescue branch — the procedure's
   entire safety net — preserves nothing.

2. **Drain has no concept of an environment kill.** No skill text matches an
   account-wide API error ("You've hit your weekly limit", auth revocation,
   hard rate-limit). Untreated, drain's step-3 routing counts the death as a
   failed attempt (escalating tiers on relaunch), and the slot machine /
   baton pass relaunches into the same wall — burning attempts, tournament
   eligibility, and generations on runs that cannot succeed until the limit
   resets.

## Solution

Skill-text changes only, to `.claude/skills/drain/SKILL.md` +
`reference.md` (worker prompt included), with a plugin version bump. Doctrine
unchanged: slot machine still never *resumes* a dead run; rescue branches stay
forensic; no worker-side heartbeats.

## Requirements

- **R1 — snapshot dirty worktrees before every sweep.** In reference.md's
  rescue procedure (and everywhere it is invoked: startup sweep, step-4
  re-check), before force-removing a dead run's worktree drain runs
  `git -C <worktree> status --porcelain`; if non-empty, it first commits a
  WIP snapshot on that run's branch inside the worktree —
  `git add` scoped to repo paths (gitignored files are excluded by git
  itself, so secrets like `.dev.vars` never enter the snapshot), commit
  message `wip(rescue): <task> — swept with uncommitted work`, `--no-verify`
  — and only then force-removes the worktree and renames the branch to
  `rescue/NN-<slug>-<shortsha>` where shortsha is now the snapshot tip.
  The existing collapse-duplicate-tips and already-preserved rules apply
  unchanged. The "Residual risk" note is amended: worktree writes are no
  longer accepted losses; the snapshot is the mitigation.

- **R2 — environment-kill routing + run halt.** New reference.md subsection
  ("Environment kill"), cited from SKILL.md step 3: a worker/verifier death
  whose recorded cause is an account-wide API error (weekly/usage limit,
  authentication failure, sustained 429/5xx after harness retries) is an
  ENVIRONMENT KILL, not a task failure. Routing: it never counts toward the
  slot-machine relaunch or tournament threshold; drain writes a `## Progress`
  entry saying so explicitly (so the next drain doesn't escalate tiers),
  performs the R1-preserving sweep, flips the task to `pending`, commits, and
  then HALTS the entire run — no further dispatch, no slot-machine relaunch,
  and no baton self-relaunch (a fresh generation hits the same wall) — ending
  with a report that names the reset time when the error carries one. A
  retryable error on ONE agent while others proceed normally is not an
  environment kill; only account-wide signals halt the run.

- **R3 — workers commit incrementally.** One added line in both the
  reference.md Worker prompt and the Headless fallback prompt: commit to the
  task branch at each completed TDD step (test → feat → refactor), and always
  commit the implementation before spawning any verifier or review pass —
  never hold the full implementation uncommitted at close-out. (This shrinks
  the window R1 protects; R1 remains necessary for mid-step deaths.)

- **R4 — version bump.** Bump `.claude-plugin/plugin.json` version (currently
  0.8.8) per the repo's release convention, with a CHANGELOG/README note if
  the repo keeps one (verify at build time).

## Acceptance

- [ ] `grep -q 'status --porcelain' .claude/skills/drain/reference.md` — R1 check present in the rescue procedure
- [ ] `grep -qi 'environment kill' .claude/skills/drain/reference.md && grep -qi 'environment kill' .claude/skills/drain/SKILL.md` — R2 subsection exists and step 3 cites it
- [ ] `grep -q 'wip(rescue)' .claude/skills/drain/reference.md` — snapshot commit convention named
- [ ] `grep -qc 'before spawning any verifier' .claude/skills/drain/reference.md | grep -qx 2` — R3 line present in BOTH worker prompt and headless fallback
- [ ] `grep -qi 'no baton self-relaunch\|no baton' .claude/skills/drain/reference.md` — halt covers generations, not just this session's loop
- [ ] `claude plugin validate .` — green
- [ ] `./specs/status.sh` — queue still parses

## Out of scope

- Worker-side heartbeats (already rejected in the stale-lock spec's Out of scope).
- Resuming killed agents via SendMessage after a limit resets — slot-machine
  doctrine ("never resume a dead run") is unchanged; the rescue branch plus
  `## Progress` evidence is the hand-forward.
- Harness retry/backoff behavior and any detection of the limit before
  dispatch (no reliable pre-flight signal exists).
- Multi-session ownership (covered by specs/multi-session-coordination) and
  the in-flight specs/drain-rolling-window work.
