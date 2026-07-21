# HANDOFF: two threads — /drain whole-queue run (gen 5) + agentprof-skill-audit spec

Note: `.claude/HANDOFF.md` is already occupied by an unrelated session's
handoff (human-tasks/ynab-triage-skill work) — this file uses a distinct
name to avoid clobbering it. Do not delete or edit `.claude/HANDOFF.md`.

## Task

Two independent threads run by this session, both still open:

**Thread A — whole-queue `/drain` run.** User-authorized ("drain
everything", re-invoked `/drain`, then "continue" after an interruption).
Now on **generation 5** (background agent id `a526e9210f7e5ab37`, launched
and still running as of this handoff — do not spawn a duplicate). Run-token
`a750d87976c02e32`.

**Thread B — new spec `specs/agentprof-skill-audit/SPEC.md`.** User asked
for a skill that reviews chat logs (like `agentprof`) for skill trigger/
outcome analysis during skill development. Ran `/idea`: scouted `agentprof`

- `evals/` + transcript format (4 scouts), ran a `deep-research` pass on
  frontier trajectory-evaluation literature, interviewed the user (7
  questions across 2 rounds), wrote the spec. **Currently in `/critique`**
  (background agent id `a5b55021045a7e085`, still running as of this
  handoff — do not spawn a duplicate critique). This is a `/critique` retry:
  the first attempt (id `a845984c2059f9518`) died from the same spend-limit
  event as drain generation 4.

## State

**Thread A history:** gen1 (this session) landed `human-blocker-impact-clarity`
(4/4 done, released), `prompt-tweaking-roi` (1/1 done, released) — batoned.
gen2 landed `drain-frontier-scanner` (done, released), `drain-session-naming-
always-propose` (done, released), reclaimed a confirmed-stale 3-spec lease,
started `drain-multi-spec-swarm`/`eval-coverage-tiers` — batoned. gen3
continued both — batoned to gen4 (`specs/eval-coverage-tiers/DRAIN-BATON.md`,
per its commit message: landed `drain-multi-spec-swarm` task 02,
`eval-coverage-tiers` task 04, `drain-multi-spec-swarm`'s spec-completion
review — 0 findings, 3 discovered, lease released — plus `eval-coverage-
tiers` tasks 05, 06). gen4 flipped `eval-coverage-tiers`/07 to in-progress,
then **died mid-dispatch from the account's monthly spend limit** (the human
has since raised it via `/rate-limit-options`). This session ran the
Environment-kill sweep: confirmed no worker branch/worktree existed for
task 07 (nothing lost), reset it to `pending` (commit `7db4ece`, pushed).
Per doctrine, halted rather than auto-relaunching; the human said "continue"
so generation 5 was spawned to resume. gen4's baton file
(`specs/eval-coverage-tiers/DRAIN-BATON.md`) is missing from disk despite a
commit claiming to have written it — not investigated further, gen5 was told
to run a fresh inventory rather than trust it.

**Thread B state:** `specs/agentprof-skill-audit/SPEC.md` written (no
`## Open questions` — none named a tech/architecture choice, so no `/design`
chain was needed). Awaiting the retry critique's verdict.

## Exact next steps for the resuming session

**Thread A:** wait for generation 5's notification. If it batoned again,
spawn the next generation the same way (Agent tool, `subagent_type: "claude"`,
`run_in_background: true`, self-contained prompt: adopt the newest
`DRAIN-BATON.md` — search `specs/*/DRAIN-OWNER.md` for the live
`Run-token` if the baton file is again missing — follow
`.claude/skills/drain/SKILL.md`, reuse `.claude/worktrees/drain-orchestrator`,
emit `agentprof` markers, keep going per R1). If it reached the batch
interview / exit checklist, the run is done — relay it.

**Thread B:** wait for the critique verdict. On READY (or READY WITH NITS
after a mechanical-findings fix loop, capped at 2-4 cycles per
`.claude/rules/token-discipline.md`), confirm `Breakdown-ready: true` got
written to the SPEC.md header, then self-chain `/breakdown` on it (Skill
tool, per CLAUDE.md's self-chain conventions — a critic-READY artifact,
model-invocable target, user hasn't scoped the request to spec-only). On
NOT READY, relay findings and fix per the critique skill's triage (apply
MECHANICAL findings directly, present JUDGMENT findings to the user before
applying). If `/breakdown` completes and the human's live request already
authorized draining ("drain everything" is still standing scope, not scoped
to a snapshot of `specs/` as it existed when first said), the new
`agentprof-skill-audit` spec's tasks become part of Thread A's queue
automatically — generation 5+ was told to check for it during 3b
auto-breakdown, but if `/breakdown` runs it directly in this thread first
that's fine too, whichever happens first.

## Files touched this session (partial — see git log for full detail,

commits are the authoritative record)

- Thread A: see per-generation baton "Done / next" sections in git history
  (`git log --oneline --grep='baton pass'`) for the full per-task file list;
  too large to re-list here.
- Thread B: `specs/agentprof-skill-audit/SPEC.md` (new).

## Gotchas

- **Account spend-limit hit mid-run** (both a critique dispatch and drain
  generation 4 died from it in the same short window) — already raised by
  the human, but a resuming session should watch for `status: failed` /
  "monthly spend limit" in task-notifications and treat it as an
  Environment-kill event (sweep in-progress locks after confirming no
  worker artifacts exist, reset to pending, do not blindly relaunch without
  checking — see `.claude/skills/drain/reference.md`'s "Environment kill").
- `drain_frontier.py` exits 2 on any spec dir with a `Status: draft`/
  `obsolete` task file — known pre-existing scanner gap, fall back to
  verbatim header reads, not a real failure.
- Task-file merges conflict on `Status: in-progress` vs `Status: done`
  essentially every time — always resolve to `done`.
- A repo formatter/linter hook fires on Edit/Write of markdown files —
  re-read before a follow-up Edit targeting a just-reformatted region.
- A `DRAIN-BATON.md` can apparently vanish between being committed and a
  later generation reading it (observed this session, gen4→gen5 boundary,
  cause not diagnosed) — a resuming session should not assume a baton file
  it expects to find is actually still there; re-derive state from
  `DRAIN-OWNER.md` + a fresh `drain_frontier.py` inventory if it's missing.
- Another live local Claude Code session (`claude-9d` in
  `claude agents --json`) shares this repo's cwd on unrelated work — not a
  collision.

## Verification

Thread A: every `done` task already passed drain's own merge-time
whitelist-diff + gate checks before merging — not re-verified here.
Thread B: nothing merged yet — spec is pre-implementation, verification
happens at `/breakdown` → `/build`/`/drain` time per its own acceptance
criteria (production rigor, TDD required).
