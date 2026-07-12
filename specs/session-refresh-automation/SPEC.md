# Automated session refresh for long-lived autonomous sessions

Status: open
Priority: P1
Breakdown-ready: false

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
  refresh-over-carry; (c) defaults for the budget (proposed: 3 re-primes or
  a 200k-token context, tunable) with the 2026-07-11 evidence cited from
  this spec, not restated. The subsection cites drain-wake-cost for the
  drain-specific baton and does not restate it.
- R2 **Refresh trigger hook.** A hook script (toolkit-shipped, wired the
  way /gate wires Stop hooks) that, on session wake/prompt-submit, derives
  the session's re-prime count and current context size from its own
  transcript (same parse-time rule agentprof uses: main-loop call past the
  first whose cache write exceeds the threshold) and, past the R1 budget,
  injects a directive: "over wake budget — write a handoff (/handoff) and
  end instead of continuing." Deterministic, no model call, silent under
  budget; unit-tested against synthetic transcript fixtures both sides of
  the budget. The hook only injects the directive — the session (or its
  human) acts on it; the hook never kills work mid-task.
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
  needs-attention inbox flags a LIVE session (already scanned by the
  workboard) whose current-window `sessions`/`reprime` summary data shows
  re-primes ≥ the R1 budget — sourced from the same summary JSON the cost
  panel already reads (specs/workboard-weekly-cost-view path); no new
  endpoint. The flag names the session, its re-prime count, and their cost.

## Out of scope

- Harness/TTL changes, or inferring exact TTL expiry from timestamps.
- Drain's baton internals (specs/drain-wake-cost owns them) and any change
  to drain's sanctioned relaunch carve-out.
- agentprof changes — the reprime label and summary sections it needs are
  shipped (specs/cache-reprime-visibility).
- New detached-execution mechanisms of any kind.

## Acceptance criteria

- [ ] `grep -ci 'wake budget' .claude/rules/token-discipline.md` ≥ 1 and
  `grep -ci 'refresh-over-carry' .claude/rules/token-discipline.md` ≥ 1
  (both phrases confirmed absent at authoring time) (R1)
- [ ] The R2 hook script exists in the toolkit with a runnable test
  (`bash` or `pytest`, per its language) proving: over-budget synthetic
  transcript → directive emitted; under-budget → empty output, exit 0 (R2)
- [ ] `grep -ci 'refresh' .claude/skills/handoff/SKILL.md` ≥ 1 with the
  autonomous path documented, and the skill's text cites the
  token-discipline detachment policy rather than restating it (R3)
- [ ] `bash agent-console/scripts/check.sh` passes; the workboard
  needs-attention renderer shows the re-prime flag when a live session's
  summary data crosses the budget and omits it otherwise, covered by a
  renderer test (R4)
- [ ] A fresh session asked "should a watcher loop run on the session
  model?" answers from R1's subsection (manual check, noted in the
  closing task's evidence) (R1)

## Open questions

- Budget defaults: 3 re-primes / 200k context are proposed from one
  night's data — confirm against the 30-day profile before pinning.
- Hook placement: global (`~/.claude/settings.json`) so it covers every
  repo's sessions, vs toolkit-repo-scoped first. Global reach is the
  point; global hooks are user-owned config (update-config territory).
- Whether R2 can read reprime counts cheaply enough at prompt-submit time
  on very large transcripts (streaming tail-parse vs full parse).

## Parallelization

Not breakdown-ready until the open questions are answered (budget
defaults and hook placement gate R1/R2 wording). Expected shape: 01 = R1
doctrine; 02 = R2 hook (after 01 pins the budget); 03 = R3 handoff text
(after 01); 04 = R4 workboard flag (independent of 02/03, after 01).
