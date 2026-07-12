# Automated session refresh for long-lived autonomous sessions

Status: open
Priority: P1
Breakdown-ready: true

## Problem

Cache re-priming cost $353 of the 2026-07-11 overnight window's $1,366
(26%), measured with agentprof's reprime label (specs/
cache-reprime-visibility, shipped). The shape: a long-lived autonomous
session idles past the 5-minute prompt-cache TTL between wakes, then
rewrites its entire accumulated context at cache-write rates before doing
any work. Worst case: one 21-hour home-directory orchestrator paid $172
across 18 re-primes (9.6M cache tokens rewritten, individual main-loop
writes up to 744k tokens) on a frontier-tier main loop. Four watch-then-act
loop sessions paid $36 of their $95 (38%) purely re-warming cache to poll.

Existing coverage ends at drain's border: specs/drain-wake-cost gave
drain-shaped sessions a verdict-count baton trigger, and
specs/cache-reprime-visibility made re-primes measurable (reprime label,
`reprime`/`sessions` summary sections, workboard line). But freehand
orchestrators, self-paced wakeup loops, and watch-then-act sessions have
no refresh mechanism at all: nothing tells a session "your next wake will
cost $9 before it does anything — hand off instead," and nothing surfaces
a live session that is bleeding re-primes while it runs.

A constraint shapes the solution space: detached self-relaunch is
policy-banned outside drain's scoped carve-out
(.claude/rules/token-discipline.md, "Awaited children, never detached").
Refresh automation must therefore work through sanctioned mechanisms —
cheap-tier holding patterns, awaited fresh workers, handoff artifacts, and
human-visible flags — not by generalizing detached respawns.

## Solution

Three layers, cheapest first: doctrine that prevents the expensive shape
from being built (a frontier main loop that waits), an automated in-session
trigger that tells a session when it has crossed its wake budget, and a
live workboard flag so a bleeding session is visible while it still runs.

## Requirements

- R1 **Wake-budget doctrine.** `.claude/rules/token-discipline.md` gains a
  "Session refresh" subsection stating: (a) a main loop that expects to
  idle past the prompt-cache TTL is a scheduler, not a thinker — long-lived
  waiting/polling runs on a cheap-tier main loop (or launchd), dispatching
  judgment work per-event to awaited fresh subagents, never on a
  frontier-tier main loop; (b) every autonomous session carries a wake
  budget — when re-primes observed or estimated context re-write cost
  crosses it, the session refreshes (writes a handoff artifact and ends, or
  batons where a sanctioned baton exists) instead of sleeping again —
  refresh-over-carry; (c) budget defaults, pinned from the 30-day profile
  (2026-06-12→07-12: 167 sessions re-primed, per-session count p50=3
  p90=10 max=23, $1.90 median per event, $1,838 total; main-loop context
  p50=151k p90=393k): 3 re-primes or a 250k-token context, tunable. Three
  is the median deliberately — the median is the behavior being changed —
  and 250k sits between the context p50 and p90 so the flag marks the
  heavy tail, not normal sessions. The subsection cites drain-wake-cost
  for the drain-specific baton and does not restate it.
- R2 **Refresh trigger hook.** A hook script (toolkit-shipped, installed
  globally via `~/.claude/settings.json` so it covers every repo's
  sessions — global reach is the point) that, on session wake/
  prompt-submit, obtains the session's re-prime count and context size
  and, past either arm of the R1 budget, injects a directive: "over
  wake budget — write a handoff (/handoff) and end instead of
  continuing." The session id comes from the hook's stdin payload (the
  harness's prompt-submit hook input carries it); the context arm reads
  `sessions.<id>.p90_ctx` — the same percentile measure R4 uses, so the
  hook and the workboard never disagree about which sessions are heavy. agentprof is the single source of the re-prime definition:
  the hook shells out to the `agentprof` binary (R2a below) rather than
  re-implementing the parse-time rule — a re-tuned `--reprime-threshold`
  must never make the hook and the profiler disagree. Binary absent or
  erroring → silent no-op, exit 0 (a missing profiler must not break
  every session). Deterministic, no model call, silent under budget;
  unit-tested against synthetic transcript fixtures both sides of the
  budget and with the binary absent. The hook only injects the
  directive — the session (or its human) acts on it; the hook never
  kills work mid-task.
- R2a **Per-session query surface in agentprof.** So the hook (R2) and
  the workboard flag (R4) read one definition, the `--summary` `sessions`
  section gains two additive per-session fields: `reprime_count` and
  `reprime_cost_microusd` (the session's samples carrying
  `reprime=true`). Existing field names are unchanged; older summary
  JSON without the fields parses as before. For the hook's
  single-session case, `agentprof claude` scoped by `--since` plus a jq
  filter on the session id suffices — no new subcommand unless
  implementation finds the full-directory parse too slow at
  prompt-submit time, in which case a `--session <id>` filter flag is
  the sanctioned addition.
- R3 **Handoff-and-terminate procedure for autonomous loops.** The
  /handoff skill documents an autonomous path: when a session refreshes
  under R2's directive, it writes the standard handoff file, surfaces the
  resume pointer where the loop's restart will find it (the loop prompt's
  next firing, a scheduled fresh session, or the attended parent), and
  ends its turn — explicitly NOT spawning a detached continuation
  (cite the token-discipline detachment policy). For self-paced loop
  wakeups this means: final wakeup fires a fresh session against the
  handoff artifact rather than waking the fat session again.
- R4 **Live re-prime flag on the workboard.** The agent-console workboard
  needs-attention inbox flags a live session over the R1 budget on EITHER
  arm: `sessions.<id>.reprime_count` ≥ 3 (the R2a fields) OR
  `sessions.<id>.p90_ctx` ≥ 250k. Join rule: the workboard's existing
  live-session scan supplies the live set; its session ids are matched
  exactly against the summary's `sessions` keys; live sessions absent
  from the summary (too new for the last refresh) are simply not
  flagged, and the flag line carries the summary file's mtime so
  staleness is visible. The flag is explicitly best-effort: its
  freshness is bounded by what regenerates the summary — the
  `com.sjaconette.agentprof-refresh` launchd job plus the workboard's
  on-demand refresh control (both run
  `agentprof/scripts/refresh-profile.sh`) —
  and the mtime line makes that bound visible rather than hiding it.
  Sourced from the same summary JSON the cost panel already reads
  (specs/workboard-weekly-cost-view path); no new endpoint. The flag names the session, which arm tripped, the re-prime
  count, and its cost.

## Out of scope

- Harness/TTL changes, or inferring exact TTL expiry from timestamps.
- Drain's baton internals (specs/drain-wake-cost owns them) and any change
  to drain's sanctioned relaunch carve-out.
- agentprof changes beyond R2a's additive per-session fields (and the
  conditional `--session` flag it sanctions) — the reprime label and the
  base summary sections are shipped (specs/cache-reprime-visibility).
- New detached-execution mechanisms of any kind.

## Acceptance criteria

- [ ] `grep -ci 'wake budget' .claude/rules/token-discipline.md` ≥ 1 and
  `grep -ci 'refresh-over-carry' .claude/rules/token-discipline.md` ≥ 1
  (both phrases confirmed absent at authoring time) (R1)
- [ ] The R2 hook script exists in the toolkit with a runnable test
  (`bash` or `pytest`, per its language) proving: over-budget synthetic
  transcript → directive emitted; under-budget → empty output, exit 0;
  agentprof binary absent → empty output, exit 0 (R2)
- [ ] `cd agentprof && go test ./internal/costsummary/` passes; the
  summary's `sessions` entries carry `reprime_count` and
  `reprime_cost_microusd`, existing field names unchanged; and
  `grep -c 'reprime_count' agentprof/SCHEMA.md` ≥ 1 (field name absent
  from SCHEMA.md at authoring time) (R2a)
- [ ] `grep -ci 'refresh-over-carry' .claude/skills/handoff/SKILL.md` ≥ 1
  (phrase confirmed absent at authoring time) with the autonomous path
  documented, and the skill's text cites the token-discipline detachment
  policy rather than restating it (R3)
- [ ] `bash agent-console/scripts/check.sh` passes; the workboard
  needs-attention renderer shows the re-prime flag when a live session's
  summary entry crosses either budget arm, omits it when under budget or
  when the session id is absent from the summary, and renders the
  summary mtime — covered by a renderer test for all three cases (R4)
- [ ] The task carrying the R3 SKILL.md edit (and any other task editing
  `.claude/skills/*` files) lists the `antigravity/` mirror and a
  `.claude-plugin/plugin.json` version bump in its `Touch:`, and
  `claude plugin validate .` passes (CLAUDE.md's mirror rule) (R3)
- [ ] A fresh session asked "should a watcher loop run on the session
  model?" answers from R1's subsection (manual check, noted in the
  closing task's evidence) (R1)

## Open questions

All resolved 2026-07-12:

- Budget defaults: pinned in R1 from the 30-day profile (3 re-primes /
  250k context).
- Hook placement: global (`~/.claude/settings.json`) — pinned in R2. The
  toolkit ships the script and documents the wiring; installing into the
  user-owned global settings is a documented step, not a repo hook.
- Prompt-submit cost: resolved by R2's shell-out design; R2a sanctions a
  `--session` filter flag if the full parse proves too slow.

## Parallelization

Task map: 01 = R1 doctrine (pins budget wording others cite); 02 = R2a
agentprof fields (independent of 01; Touch is agentprof/ only);
03 = R2 hook (after 01 and 02); 04 = R3 handoff text (after 01);
05 = R4 workboard flag (after 02; Touch is agent-console/ only,
disjoint from 03/04).

- Group: 01, 02
- Group: 04, 05
