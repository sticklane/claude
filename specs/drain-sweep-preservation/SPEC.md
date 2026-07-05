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

1. **The sweep can destroy the only copy of finished work.** The rescue
   procedure (reference.md "Status field semantics", the `Force-remove each
   worktree FIRST` step) removes each worktree before renaming branches;
   SKILL.md restates it inline in step 1 ("force-removing each worktree
   first") and step 3's `## Progress` paragraph asserts "Worktree writes are
   discarded with failed branches". That is correct for task failures
   (slot-machine doctrine) but wrong in the common crash case: a worker that
   dies between finishing implementation and its close-out commit leaves a
   dirty worktree and an EMPTY branch. The rescue branch — the procedure's
   entire safety net — preserves nothing.

2. **Drain has no concept of an environment kill.** No skill text matches an
   account-wide API error ("You've hit your weekly limit", auth/billing
   failure, sustained 429/5xx after harness retries). Untreated, drain's
   step-3 routing counts the death as a failed attempt (escalating tiers on
   relaunch), and the slot machine / baton pass relaunches into the same
   wall — burning attempts, tournament eligibility, and generations on runs
   that cannot succeed until the limit resets.

## Solution

Skill-text changes only, to `.claude/skills/drain/SKILL.md` +
`reference.md` (worker prompts included), with a plugin version bump. Doctrine
unchanged: slot machine still never *resumes* a dead run; rescue branches stay
forensic; no worker-side heartbeats; one writer.

## Requirements

- **R1 — snapshot dirty worktrees before every sweep.** Amend reference.md's
  rescue procedure (Status field semantics) so that before force-removing a
  dead run's worktree drain runs `git -C <worktree> status --porcelain`; if
  non-empty, it first commits a WIP snapshot on that run's branch inside the
  worktree — exactly `git add -A` from the worktree root (git itself excludes
  gitignored files, so `.dev.vars`/`node_modules` never enter the snapshot),
  then `git commit --no-verify -m "wip(rescue): <task> — swept with
  uncommitted work"` — and only then force-removes the worktree and renames
  the branch to `rescue/NN-<slug>-<shortsha>`, where shortsha is now the
  snapshot tip. The existing collapse-duplicate-tips and already-preserved
  rules apply unchanged. Every OTHER sweep-invoking text defers to this one
  procedure rather than restating it: SKILL.md step 1's inline sweep sentence
  gains "(snapshotting uncommitted worktree changes per reference.md's rescue
  procedure)" or equivalent; reference.md's step-4 re-check and headless
  cleanup already cite the rescue procedure and need no separate copy.
  Two adjacent statements are corrected in place:
  - SKILL.md step 3's parenthetical "(Worktree writes are discarded with
    failed branches; this record survives because drain … writes it in the
    main checkout.)" is reworded: worktree writes are preserved in the rescue
    snapshot when a dead run is swept dirty; deliberately DISCARDED branches
    (slot-machine losers, non-winning tournament candidates) remain
    discarded — `## Progress` still lives in the main checkout.
  - reference.md's "Residual risk (accepted)" note (false sweeps of live
    workers going activity-silent) gains one sentence: a false sweep now also
    snapshots the live worker's uncommitted writes onto the rescue branch, so
    the accepted risk is losing the RUN, not the work.

- **R2 — environment-kill routing + run halt.** New reference.md subsection
  ("Environment kill"), cited from SKILL.md step 3 next to the sweep-race
  note. **Detection signal (drain-side; a dead worker cannot self-report):**
  the harness's completion/failure notification for a background worker
  carries the termination cause (e.g. `Agent terminated early due to an API
  error: <message>`); drain classifies the kill as environmental when that
  message — or an API error drain's own session hits — names an account-wide
  condition: usage/weekly limit (with reset time), authentication or billing
  failure, or persistent 429/5xx surviving harness retries. An error on ONE
  agent while other live agents proceed normally is NOT an environment kill;
  only account-wide signals qualify. **Routing:** an environment kill never
  counts toward the slot-machine relaunch or tournament threshold; because
  the death signal is definitive, the sweep proceeds immediately — the
  15-minute stale-lock grace window does not apply. **Halt is run-wide, not
  per-task:** an account-wide error has killed or will kill every live
  worker, so drain sweeps EVERY currently-live run — all in-progress tasks it
  owns, all tournament entrants, all group members — with the R1-preserving
  procedure, writes each task's `## Progress` entry stating "environment
  kill, does not count as an attempt", flips each to `pending`, commits and
  pushes, then HALTS: no further dispatch, no slot-machine relaunch, and no
  baton self-relaunch (a fresh generation hits the same wall). The final
  report names the reset time when the error carries one. Tasks owned by a
  FOREIGN orchestrator (per any committed partition/owner record) are left
  alone — one writer; absent any such record, every live run is drain's own
  and is swept.

- **R3 — workers commit incrementally.** The reference.md Worker prompt and
  the Headless fallback prompt both gain the clause: commit to the task
  branch at each completed TDD step (test → feat → refactor). The Worker
  prompt (which spawns a verifier; the headless prompt does not) additionally
  says: always commit the implementation before spawning any verifier or
  review pass — never hold the full implementation uncommitted at close-out.
  (This shrinks the window R1 protects; R1 remains necessary for mid-step
  deaths.)

- **R4 — version bump.** Bump `.claude-plugin/plugin.json` version (0.8.8 at
  spec time) per the repo's release convention, with a CHANGELOG/README note
  if the repo keeps one (verify at build time).

## Acceptance

- [ ] `grep -q 'status --porcelain' .claude/skills/drain/reference.md` — R1 dirty check present in the rescue procedure
- [ ] `grep -q 'wip(rescue)' .claude/skills/drain/reference.md` — snapshot commit convention named, with `git add -A` pinned nearby
- [ ] `grep -qi 'snapshotting uncommitted' .claude/skills/drain/SKILL.md` — step 1's inline sweep sentence defers to the snapshotting procedure (the bare word "snapshot" appears in SKILL.md today in an unrelated merge note — this check pins R1's exact new fragment)
- [ ] `grep -qi 'preserved in the rescue snapshot' .claude/skills/drain/SKILL.md` — step 3's discard parenthetical reworded per R1 (positive assertion; the old phrase is line-wrapped, so a negative single-line grep passes trivially today)
- [ ] `grep -qi 'environment kill' .claude/skills/drain/reference.md && grep -qi 'environment kill' .claude/skills/drain/SKILL.md` — R2 subsection exists and step 3 cites it
- [ ] `grep -qi 'account-wide' .claude/skills/drain/reference.md` — R2 names the detection signal class
- [ ] `grep -Eqi 'grace window does not apply|window does not apply' .claude/skills/drain/reference.md` — R2 bypasses the stale-lock window
- [ ] `grep -qi 'no baton self-relaunch' .claude/skills/drain/reference.md` — halt covers generations, not just this session's loop
- [ ] `[ "$(grep -c 'at each completed TDD step' .claude/skills/drain/reference.md)" -eq 2 ]` — R3 incremental-commit clause in BOTH the Worker prompt and the Headless fallback
- [ ] `[ "$(grep -c 'before spawning any verifier' .claude/skills/drain/reference.md)" -eq 1 ]` — verifier-specific clause in the Worker prompt only (headless has no Task tool)
- [ ] `claude plugin validate .` — green
- [ ] `./specs/status.sh` — queue still parses

## Out of scope

- Worker-side heartbeats (already rejected in the stale-lock spec's Out of scope).
- Resuming killed agents via SendMessage after a limit resets — slot-machine
  doctrine ("never resume a dead run") is unchanged; the rescue branch plus
  `## Progress` evidence is the hand-forward.
- Harness retry/backoff behavior and any detection of the limit before
  dispatch (no reliable pre-flight signal exists).
- Multi-session ownership and owner leases (specs/multi-session-coordination)
  and the in-flight specs/drain-rolling-window work; R2 only REQUIRES
  respecting whatever partition/owner records exist at halt time.
