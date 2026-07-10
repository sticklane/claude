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

Add a **remote divergence check** to drain's step 1, positioned to run
**before step 1's Status-header read** (today's first action in step 1,
ahead of the owner-lease claim) — not merely "before the lease claim,"
since the lease claim already comes after the Status-header read today,
and this check exists specifically so that read sees current state:
`git fetch <remote>`, then compare local `main` against `<remote>/main`.

- **No remote configured** → skip silently, identical to the existing
  push guard's no-remote behavior.
- **Remote configured but `git fetch` itself fails** (network down,
  auth/DNS failure — distinct from "no remote configured") → warn and
  continue with the local view, identical to the push guard's existing
  offline/rejected behavior. This check degrades to today's behavior on
  a transient failure; it does not block the run on connectivity issues.
- **No new remote commits** (`git log main..<remote>/main` empty) →
  proceed exactly as today.
- **New remote commits exist, no local unpushed commits**
  (`git log <remote>/main..main` empty) → fast-forward local `main` to
  `<remote>/main` (`git merge --ff-only`, always safe — this session has
  nothing of its own to lose) before the Status-header read, so
  `Status:` lines, leases, and specs reflect current shared state.
- **New remote commits exist AND local unpushed commits exist** (true
  divergence — this session has already committed work not yet on the
  remote) → HALT this drain invocation before claiming the lease. Do not
  merge automatically, do not force-push, do not discard either side, and
  do NOT attempt a live/blocking interactive prompt (drain is
  `disable-model-invocation`, launched unattended by default — a
  mid-run prompt would block on a human who may not be watching, and
  freeze any in-flight rolling-window workers). Instead: stop the run
  cleanly and emit the divergence (commit counts/subject lines on each
  side) as this invocation's final message, in the same shape as an
  end-of-run blocker report — the human who eventually reads it decides
  next steps (mirroring what worked in the 2026-07-08 incident: take
  theirs, merge both, or reconcile manually), per
  `.claude/rules/concurrent-sessions.md`. An ATTENDED session (a human
  actively watching, like the one that resolved the 2026-07-08 incident)
  may additionally use AskUserQuestion in place of halting-and-reporting
  if a human is confirmed present — that is this session's own judgment
  call, not a behavior this spec mandates for unattended drain.

This check re-runs **before every new owner-lease claim** within a single
drain run (not just once at startup), since divergence can accumulate
mid-session on a long-running queue. This bounds the fix to per-spec-claim
granularity: divergence that occurs entirely WITHIN one spec's dispatch/
collect cycle (between its lease claim and release) is not caught until
that spec's lease is released and the next claim happens — an accepted
residual gap (R5), not a claim that this spec fully closes the exact
2026-07-08 incident's window (it is not confirmed whether that incident's
divergence accumulated within a single spec's claim or across several;
this fix catches the latter, not necessarily the former).

## Requirements

- **R1**: Before step 1's Status-header read (both on a fresh spec's
  first pass and any re-claim after the batch interview reopens a
  deferred task), drain runs `git fetch <remote>`:
  - No remote configured → skip silently (matches the push guard's
    no-remote behavior).
  - Remote configured but `git fetch` fails (network/auth/DNS) → warn
    and continue with the local view (matches the push guard's existing
    offline/rejected behavior) — this is NOT the same case as "no
    remote configured" and must be handled as its own branch, not
    conflated with it.
- **R2**: If `<remote>/main` has no commits absent from local `main`,
  proceed unchanged — this is the common case and must add no visible
  overhead to the normal path.
- **R3**: If `<remote>/main` has new commits and local `main` has no
  unpushed commits, fast-forward local `main` to `<remote>/main`
  (`git merge --ff-only`) BEFORE the Status-header read — always safe
  (never loses local work since there is none to lose), and ordered
  this way specifically so the Status-header read sees current state,
  not the pre-fetch view.
- **R4**: If `<remote>/main` has new commits AND local `main` has
  unpushed commits (true divergence), drain HALTS this invocation before
  claiming the lease — it does not attempt a live/blocking interactive
  prompt (drain is unattended by default; a mid-run prompt could block on
  an absent human and freeze in-flight workers). It reports the
  divergence (each side's commit count and subject lines) as this
  invocation's final message, in the same shape as an end-of-run blocker
  report, per `.claude/rules/concurrent-sessions.md`. Drain never
  auto-merges, auto-resolves conflicts, or force-pushes in this case. An
  attended session may choose to use AskUserQuestion instead of halting,
  at that session's own discretion — not a behavior this requirement
  mandates.
- **R5**: The check fires once per lease claim, not continuously during
  a spec's dispatch/collect cycle — a spec already claimed and being
  worked is not re-checked until its lease is released and the next
  spec (or a re-claim) begins. This is an accepted, bounded gap: this
  spec catches cross-spec-claim divergence, not divergence that
  accumulates entirely within one spec's active dispatch window.
- **R6**: `.claude/skills/drain/SKILL.md` stays genuinely under the
  repo's 500-line convention ("well under 500," per CLAUDE.md — 500 is
  the hard ceiling, not a target to land on exactly) — currently 499
  lines, already at that ceiling with zero headroom. The new contract is
  capped at a single pointer line (not "a few lines") naming the check
  and pointing to reference.md; this addition is UNCONDITIONALLY paired
  with a compensating trim of an equal or greater number of lines
  elsewhere in SKILL.md (tightening existing prose, not deleting
  content) in the same commit, so the net line delta is ≤0 regardless of
  whether the raw addition alone would cross 500 — the file must not
  land at exactly 500 with no margin left for the next change. The full
  fetch/compare/fast-forward/halt procedure lives entirely in
  `reference.md`'s "Owner lease" section (extending it, not adding a new
  top-level section).
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
- Auto-breakdown (3b) and critique/stub intake's own lease claims — a
  DIFFERENT, accepted gap (parallel to R5's), not something R1 covers:
  3b/critique-intake/stub-intake each claim their own target spec's lease
  from inside their own section, then loop back to step 1 — so R1's fetch
  fires at that subsequent step-1 entry, AFTER the lease for that spec is
  already claimed, not before. Closing this ordering gap (making these
  paths fetch before their own lease claim, not just before the next
  step-1 pass) is out of scope for this spec; it would mean editing 3b's,
  critique intake's, and stub intake's own procedures, not just step 1's.

## Acceptance criteria

- [ ] `.claude/skills/drain/SKILL.md`'s step 1, before the Status-header
      read, names the remote divergence check in a single pointer line
      to reference.md — the commit pairs it with an unconditional
      compensating trim elsewhere in the file, so `wc -l
      .claude/skills/drain/SKILL.md` stays strictly below 500 (genuine
      headroom left, not landing at exactly 500) (R6).
- [ ] `reference.md`'s "Owner lease" section contains the full fetch/
      compare/fast-forward/halt procedure with exact git commands,
      including the no-remote-vs-fetch-failure distinction (R1) and the
      halt-not-live-prompt mechanism for true divergence (R4).
- [ ] A fixture: local `main` behind `<remote>/main`, no local unpushed
      commits → the documented procedure fast-forwards before the
      Status-header read (inspectable on the reference.md prose, or
      exercised against a scratch git repo if practical within budget)
      (R3).
- [ ] A fixture: local `main` AND `<remote>/main` both have commits the
      other lacks (true divergence) → the documented procedure halts and
      reports as a final-message blocker rather than merging/resolving
      automatically or attempting a live interactive prompt (R4).
- [ ] A fixture: remote configured but `git fetch` fails → the documented
      procedure warns and continues with the local view, distinctly from
      the no-remote-configured case (R1).
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

## Parallelization

Single task (01-remote-divergence-check.md) — R7 requires the antigravity
mirror and plugin bump to land in the same commit as the core SKILL.md/
reference.md change, so this cannot be split into independently-landable
tasks. No grouping applies.
