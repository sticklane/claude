# drain: detect remote divergence before claiming a lease, not just at push time

Priority: P1

## Problem

Drain's only signal that a concurrent process is working the same repo is
a rejected `git push` — which fires only when THIS session attempts to
push, and only after it has already committed (and possibly dispatched
workers, merged branches, and released leases against) a view of the
repo that was already stale. On 2026-07-08/09, two independent drain
sessions worked `/Users/sjaconette/claude` concurrently: one direct-push
(this session), one PR-based (branch
`claude/sdlc-vibe-coding-harness-37ftxf`, merged via GitHub PRs). Neither
saw the other — drain's existing "Startup session sweep" only checks
LOCAL live sessions (`claude agents --json` / `~/.claude/sessions/*.json`
pid records), which is blind to a session on another machine, a cloud/
remote agent, or a PR-based workflow that doesn't share this machine's
session records at all. By the time the direct-push session's `git push`
was finally rejected, ~90 commits had landed on `origin/main`, including
independent, duplicate implementations of the same two tasks the
direct-push session had also just completed — wasted work, and a
conflicted merge that took manual reconciliation to resolve safely.

The fix is not a better local sweep (the other session was invisible to
any local check) — it is checking the actual shared source of truth,
`origin/main`, before trusting the local view for dispatch decisions.

## Solution

Add a **remote divergence check** to drain's owner-lease claim (step 1),
immediately before the write-if-absent / CAS lease claim: `git fetch
<remote>` (silently skip if no remote is configured, same guard as the
existing push guard), then compare local `main` against `<remote>/main`.

- **No new remote commits** (`git log main..<remote>/main` empty) →
  proceed exactly as today.
- **New remote commits exist, no local unpushed commits**
  (`git log <remote>/main..main` empty) → fast-forward local `main` to
  `<remote>/main` (`git merge --ff-only`, always safe — this session has
  nothing of its own to lose) before proceeding to inventory, so
  `Status:` lines, leases, and specs reflect current shared state.
- **New remote commits exist AND local unpushed commits exist** (true
  divergence — this session has already committed work not yet on the
  remote) → STOP. Do not merge automatically, do not force-push, do not
  discard either side. Surface it to the user exactly as the
  concurrent-sessions rule already prescribes for a detected collision
  (`.claude/rules/concurrent-sessions.md`): report what diverged (commit
  counts/subjects on each side), and let the user decide (their options
  mirror what worked in the 2026-07-08 incident: take theirs, merge both,
  or stop for manual reconciliation) — never guess.

This check re-runs **before every new owner-lease claim** within a single
drain run (not just once at startup), since divergence can accumulate
mid-session on a long-running queue (the 2026-07-08 incident's ~90 commits
landed WHILE the direct-push session was actively dispatching, not before
it started). It does not re-run mid-dispatch of an already-claimed spec —
only at the natural per-spec checkpoint drain already has.

## Requirements

- **R1**: Before each owner-lease claim in step 1 (both the initial claim
  for a fresh spec and any re-claim after the batch interview reopens a
  deferred task), drain runs `git fetch <remote>` — skip silently if no
  remote is configured, identical to the existing push guard's no-remote
  behavior.
- **R2**: If `<remote>/main` has no commits absent from local `main`,
  proceed unchanged — this is the common case and must add no visible
  overhead to the normal path.
- **R3**: If `<remote>/main` has new commits and local `main` has no
  unpushed commits, fast-forward local `main` to `<remote>/main`
  (`git merge --ff-only`) before proceeding — always safe, never loses
  local work since there is none to lose.
- **R4**: If `<remote>/main` has new commits AND local `main` has
  unpushed commits (true divergence), drain stops before claiming the
  lease: reports the divergence (each side's commit count and subject
  lines) to the user and asks how to proceed, per
  `.claude/rules/concurrent-sessions.md`. Drain never auto-merges,
  auto-resolves conflicts, or force-pushes in this case.
- **R5**: The check fires once per lease claim, not continuously during
  a spec's dispatch/collect cycle — a spec already claimed and being
  worked is not re-checked until its lease is released and the next
  spec (or a re-claim) begins.
- **R6**: `.claude/skills/drain/SKILL.md` stays a short contract + pointer
  (the file is already at the repo's 500-line convention ceiling); the
  full fetch/compare/fast-forward/stop procedure lives in
  `reference.md`'s "Owner lease" section (extending it, not adding a new
  top-level section) or a clearly-linked sibling section — implementer's
  call on the cleanest fit, but SKILL.md's own net line delta must stay
  small (a few lines, not a restatement of the procedure).
- **R7**: Port the equivalent contract to
  `antigravity/.agents/workflows/drain.md` in the same commit, in that
  mirror's own paraphrased voice per
  `docs/memory/workboard-mirror-verbatim.md` (prose-skill mirrors are
  paraphrased ports, not byte-identical) — this is a queue-mechanics
  change, not a self-chaining behavior, so it is NOT covered by
  `antigravity/README.md`'s "self-chaining not ported" carve-out
  (confirm this distinction holds before citing it either way).
- **R8**: `.claude-plugin/plugin.json`'s version is bumped, per CLAUDE.md's
  convention for a skill-behavior change.

## Out of scope

- Any change to the existing push guard (push-after-every-commit,
  skip-if-no-remote) — this spec only adds a pre-lease-claim check, it
  does not change when or whether drain pushes.
- Any change to the LOCAL session sweep (`claude agents --json`) — that
  check stays as an advisory complement; this spec adds the remote-facing
  check the sweep cannot provide, it does not replace the sweep.
- Continuous/polling divergence checks during a spec's active dispatch —
  out of scope per R5; the per-lease-claim cadence is the whole fix.
- Automatic conflict resolution for the true-divergence case (R4) — the
  2026-07-08 incident showed this genuinely needs a human's judgment call
  (which side's redundant work to discard), not a fixed algorithm.
- Auto-breakdown (3b) and critique/stub intake's own lease claims — R1's
  "before each owner-lease claim" already covers these, since they claim
  the same `DRAIN-OWNER.md` mechanism; no separate requirement needed for
  them specifically.

## Acceptance criteria

- [ ] `.claude/skills/drain/SKILL.md`'s owner-lease-claim step names the
      remote divergence check (fetch, fast-forward-if-clean,
      stop-if-diverged) in a few lines, pointing to reference.md for the
      full procedure — `wc -l .claude/skills/drain/SKILL.md` stays at or
      under 500 lines (R6).
- [ ] `reference.md`'s "Owner lease" section (or a clearly cross-linked
      sibling) contains the full fetch/compare/fast-forward/stop
      procedure with the exact git commands (R1-R5).
- [ ] A fixture: local `main` behind `<remote>/main`, no local unpushed
      commits → the documented procedure fast-forwards before proceeding
      (inspectable on the reference.md prose, or exercised against a
      scratch git repo if practical within budget) (R3).
- [ ] A fixture: local `main` AND `<remote>/main` both have commits the
      other lacks (true divergence) → the documented procedure stops and
      reports rather than merging/resolving automatically (R4).
- [ ] `grep -c 'fetch' .claude/skills/drain/reference.md` → at least one
      match in the Owner lease section referencing this check.
- [ ] `antigravity/.agents/workflows/drain.md` carries the equivalent
      contract in its own voice — a content-coverage check (grep for the
      core concepts: fetch before lease claim, fast-forward-if-clean,
      stop-if-diverged), not a byte-identical diff (R7).
- [ ] `git diff <base-commit> -- .claude-plugin/plugin.json | grep
      '"version"'` shows the version increased (R8).

## Open questions

(none)
