# HANDOFF: /drain — whole-`specs/` queue (no-argument launch)

## Task

Continuing an unattended `/drain` run over the whole `specs/` queue (no
argument = whole-queue scope, per drain's exhaustion contract). This
session (gen 1, attended) hit the session-refresh wake budget (3
re-primes, 230k-token p90 context) after 2 recorded verdicts and wrote a
baton mid-run rather than continuing in a bloated context. **A fresh
session should just run `/drain` again** — it reads the baton below and
resumes automatically; this file exists only because the session-refresh
hook fires independently of drain's own baton mechanism.

**Primary resume artifact:** `specs/drain-multi-spec-swarm/DRAIN-BATON.md`
(generation 2, `Run-token: ab7b3e973279b470`) — this is the authoritative
state, more detailed than this file. Read it first.

**Orchestrator isolation:** this run works from an isolated worktree at
`.claude/worktrees/drain-orchestrator` (detached HEAD, currently at
`4f6d643`), NOT the primary checkout at `/Users/sjaconette/claude`. A
fresh `/drain` invocation should re-establish or reuse this isolated
worktree per its own "Orchestrator isolation" procedure — don't work
directly in the primary checkout. Since `main` is already checked out in
the primary checkout, the isolated worktree cannot check out `main` by
name (git one-worktree-per-branch) — use `git worktree add --detach
<path> main` (or `origin/main`) instead, matching what this generation
did.

## State

**Currently claimed:** `specs/drain-multi-spec-swarm` only
(`Run-token: ab7b3e973279b470`, gen 2 per the baton). No other spec lease
is held.

**Landed this generation:**

- Task 01: done (landed before this run).
- Task 04 (admission.py + touch_disjoint.py): done, merged (`aaa1638`).
- Task 06 (skill-invokes-admission): done, merged (`7567f25`). Live
  `/drain`'s SKILL.md step 1 now invokes `admission.py` for R1/R2.

**Needs redispatch (not a real blocker — see Gotchas):**

- Task 03 (mirror-and-version-bump): attempt 1 returned a **false
  BLOCKED**. Left `Status: in-progress` with a `## Progress` note
  explaining why; does not count toward slot-machine escalation.
  Redispatch with an explicit instruction to sync the worker's worktree
  against `origin/main`, not local `main`.

**Still pending, dispatchable now:**

- Task 02 (token-discipline-carveout): `Depends on: none`, P2.
- Task 05 (admission-concurrency-test): `Depends on: 04` (done), P1.

Next dispatchable by priority/tie-break: task 03 (redispatch) or task 05
(both P1, tied unblocking-power — 03 wins lexicographic tie-break, so
finish its redispatch first), then task 05, then task 02 (P2).
Spec-completion review has not run yet — runs once nothing is left to
dispatch for this spec.

**Deferred to later (never reached this generation):**

- `specs/drain-frontier-scanner` — lease was reclaimed (was stale) then
  released again in favor of `drain-multi-spec-swarm` (higher priority,
  overlapping Touch footprint, per R5). Has 2 pending tasks (03, 04) and
  1 draft stub (05). Re-claim once `drain-multi-spec-swarm` releases.
- Whole-queue inventory (before claiming this spec) found ~5 more
  dispatchable specs — `drain-session-naming-always-propose`,
  `eval-coverage-tiers`, `human-blocker-impact-clarity`,
  `prompt-tweaking-roi` — all overlap `drain-multi-spec-swarm`'s Touch
  footprint (SKILL.md, reference.md, plugin.json, antigravity mirror, or
  token-discipline.md) and could not be claimed alongside it. Re-run
  inventory fresh once this spec's lease releases.
- `specs/codebase-context-tree` (unrelated prior drain run): fully done
  (14/14), one new `Status: draft` stub (task 15) for stub intake at
  the appropriate priority — not touched this generation.

## Files touched this session

- `specs/drain-frontier-scanner/DRAIN-OWNER.md` — reclaimed then removed
  (lease released back).
- `specs/drain-multi-spec-swarm/DRAIN-OWNER.md` — claimed.
- `specs/drain-multi-spec-swarm/tasks/{03,04,06}-*.md` — status flips +
  Progress entry (03).
- `.claude/skills/drain/{SKILL.md,reference.md}`,
  `.claude/skills/drain/admission.py`,
  `.claude/skills/_shared/touch_disjoint.py`, plus their tests —
  landed via tasks 04/06.
- `specs/drain-multi-spec-swarm/evidence/{04,06}-*.md` — verifier
  reports.
- `specs/drain-multi-spec-swarm/DRAIN-BATON.md` — new, generation 2.
- Two prior-session handoffs consumed: `.claude/HANDOFF.md`
  (transcript-antipattern specs) and this file's predecessor (a mid-run
  drain handoff from an earlier generation, now superseded by this one).
- Nothing else in the repo was edited by drain this session.

## Gotchas / things learned this session (don't re-derive)

- **Local `main` in the primary checkout goes stale under orchestrator
  isolation and stays that way** — the isolated worktree pushes straight
  to `origin/main`; local `refs/heads/main` in the primary checkout only
  advances when a human runs `git pull` there. This is expected and
  harmless for the orchestrator itself, but **a dispatched worker's own
  "reset your worktree to `<default-branch>` tip" step can resolve to the
  stale local ref instead of `origin/main`** if not told explicitly which
  to target. This caused two real problems this generation: task 03's
  worker returned a false BLOCKED (concluded already-merged work hadn't
  landed); task 04's worker branched from a stale base (merged cleanly
  anyway, but only by luck — no real conflict existed). Task 06's worker
  independently caught and self-corrected this. **Fix for future
  dispatches: add an explicit line to the worker prompt naming
  `origin/main` (not bare `main`) as the sync target whenever the
  orchestrator is running from an isolated worktree.** Worth a permanent
  fix to the Worker prompt contract in reference.md — a good `/idea` or
  small spec, not done this session (discovered, not actioned).
- **Reclaiming a stale lease and then immediately re-releasing it is
  correct, not wasted motion**: this generation reclaimed
  `drain-frontier-scanner`'s dead lease (mechanical preflight sweep, 8+
  hours stale) before discovering `drain-multi-spec-swarm` was
  higher-priority and Touch-overlapping, so it released
  `drain-frontier-scanner` again and claimed the other. Both are
  legitimate, separately-committed steps per R1/R5 — don't try to
  collapse them into one commit or skip the reclaim just because it gets
  immediately superseded.
- **Almost every ready spec in this queue overlaps `drain-multi-spec-
swarm`'s Touch footprint** (it patches the shared drain-skill
  infrastructure itself: SKILL.md, reference.md, plugin.json, the
  antigravity/codex mirrors, token-discipline.md) — expect a single-spec
  claim to be normal here, not a bug, until this spec's tail (02, 03, 05)
  fully lands.
- A real local/remote divergence (local ahead 3, behind 28) at session
  start turned out to be two things: (a) a genuinely different prior
  drain generation's already-pushed work (clean rebase, no conflicts),
  and (b) unrelated uncommitted WIP in the primary checkout
  (`docs/architecture.md`, a task-tracking research doc, a stale
  pathspec-hardening handoff, a deleted root HANDOFF.md) that predates
  this session and was stashed/restored intact, never committed — still
  sitting there, not drain's concern.

## Verification

- Task 04: independent verifier PASS on all 9 criteria (in-dispatch);
  I additionally re-ran all project gates before merging — green.
- Task 06: independent verifier PASS on all 4 criteria (in-dispatch); I
  additionally re-ran all project gates before merging — green.
- Task 03: no verification owed — attempt 1 made no changes (false
  BLOCKED, no commits on its branch).
- Nothing landed this session is unverified.
