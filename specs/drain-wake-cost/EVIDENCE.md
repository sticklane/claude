# agentprof evidence — orchestration-skill cost profile (2026-07-04 → 2026-07-11)

Shared evidence base for `drain-wake-cost`, `orchestrator-share-audit`, and
`agent-tier-leaks`. Source: `agentprof claude --days 7` over `~/.claude`
transcripts — 137 sessions, 48,729 API calls, $4,998.94 API-equivalent.
Analysis ran over the canonical samples JSONL
(`agentprof claude --days 7 -o samples.jsonl`). The exact profile is pinned
at `profile-2026-07-04-to-11.pb.gz` in this directory; to reproduce the
sample window later use `agentprof claude --since 2026-07-04T00:00:00Z`
(the rolling `--days 7` window will have moved on). "Rewrite" below means a call
whose `cache_write_tokens` exceeded both `cache_read_tokens` and 50k — i.e.
the prompt prefix was not served from cache and the whole context was
re-written at 1.25× input rate.

## Headline measurements

| Measurement | Value |
|---|---|
| Main-line (orchestrator) spend | $2,841 of $4,999 (57%) |
| Whole-prefix cache rewrites | 614 calls, $1,020 (20.4% of total) |
| — of which main-line | $823 (inside workers: only $197) |
| — main-line rewrites after >5m idle gap (cache-TTL expiry) | 268 wakes, $587 |
| — main-line rewrites at <5m gap, context flat/growing (prefix invalidation) | 112 calls, $236 |
| — compaction-shaped rewrites (context shrank >30% at rewrite) | 0 |
| Rewrite size | median 187k tokens, p90 384k, max 671k |
| Heavy-session spend after context first crossed 200k | $1,279 (45% of all main-line spend) |
| Per-call cost growth q1→q4 in top sessions | 2–4× (avg context 100k → 300–600k) |

The TTL-expiry cluster matches drain's awaited-worker shape exactly: the
orchestrator awaits a worker for 5–30 minutes, its prefix falls out of the
5-minute cache window, and the verdict-collection call re-caches the entire
context. At the median rewrite size on opus input rates that is ≈$3.50 per
verdict; at a 40k orchestrator context it would be ≈$0.75.

## Orchestrator vs delegated share per skill

| Skill | main-line $ | delegated $ | orch share |
|---|---|---|---|
| /parallel | 4.54 | 25.83 | 15% |
| /drain | 194 | 186 | 51% |
| /idea | 81 | 34 | 70% |
| /build | 58 | 16 | 78% |
| /breakdown | 142 | 27 | 84% |

Note: /breakdown, /build, and /idea already carry "don't read the codebase
into this session" doctrine — the high share is NOT missing instructions.
Root cause is unmeasured (see orchestrator-share-audit).

Freehand orchestration — turns named "drain…"/"ultracode" running under
`(no skill)` — cost $1,406 across 15,072 calls, ~5× attributed skill:drain,
and contains the worst rewrite-waste sessions.

## Agent-tier economics

| Agent type | total $ | calls | $/call | model mix |
|---|---|---|---|---|
| general-purpose | 1,126 | 16,771 | 0.067 | fable $474 / opus $425 / sonnet $113 |
| agentic:implementation-worker | 609 | 10,736 | 0.057 | opus $538 (pinned) |
| agentic:verifier | 187 | 5,028 | 0.037 | sonnet $81 / **fable $74** / opus $31 |
| agentic:critic | 58 | 1,170 | 0.049 | opus $46 |
| agentic:scout | 52 | 8,637 | 0.006 | haiku (pinned) |

Structural pins (scout→haiku, implementation-worker→opus, verifier→sonnet in
`.claude/agents/*.md` frontmatter) held wherever they applied. Leaks: $74 of
verifier spend ran on fable despite the sonnet pin, and general-purpose —
the second-largest sink overall — inherits the session's frontier model and
is costlier per call than the opus-pinned implementation-worker.

Bare vs `agentic:`-prefixed agent frames (e.g. `agent:verifier` vs
`agent:agentic:verifier`) both appear; hypothesis: bare = repo-local
`.claude/agents/` in the toolkit dev checkout, prefixed = plugin-served.
Unconfirmed — see agent-tier-leaks R3.

## Follow-up (2026-07-12): post-fix verification — the dual baton trigger has NOT materially reduced reprime pileup

Answers this spec's deferred MANUAL acceptance criterion ("re-run `agentprof
claude --days 7`; main-line rewrite cost inside drain-shaped sessions
materially down vs the $587 TTL-expiry baseline"). Verdict: **not down** —
the session-level failure rate got worse, not better.

Method: `agentprof claude --days 7` re-run 2026-07-12 (window
2026-07-05→2026-07-12, 137 sessions, 334 reprime events —
`cache_write_tokens` > 50k on a non-first main-loop call, agentprof's
built-in `--reprime-threshold`). Sessions split into pre-/post-fix cohorts
by first-event timestamp against 2026-07-11T08:07:54Z, the commit time of
task 01's dual-trigger text (`1d59c04`).

| Cohort | Sessions | Reprime rate /1k calls | Sessions ≥3 reprimes | Total cost |
|---|---|---|---|---|
| Pre-fix | 87 | 6.50 | 26.4% | $2,823 |
| Post-fix | 51 | 5.59 | **29.4%** | $2,077 |

The per-call rate improved slightly, but the share of sessions that blow
past the general session-refresh doctrine's 3-reprime budget got *worse*.
The single worst session in the entire 7-day window (`6fddf102`, 18
reprimes, $463) started 2026-07-11T16:36 — 8 hours after the fix landed.

Two distinct failure modes, both post-fix:

1. **Drain sessions themselves still pile up.** Three confirmed
   `skill:drain` sessions post-fix (`55ae834e`: 11 reprimes/$115,
   `80161f1c`: 9/$207, `c2cec1dd`: 3/$173) — the shipped trigger (a
   verdict-count formula standing in for context size, per R1's own text:
   "the harness exposes no reliable in-session context-size signal the hub
   can check") is not firing early enough in practice.
2. **Freehand/non-drain long sessions dominate the rest.** `6fddf102`
   (extended multi-topic `agent:claude` session, 18 reprimes/$463),
   `789d8a1a` (a recurring ~15-minute poll loop under `skill:human-tasks`,
   9 reprimes), `a7660966`/`14fe4310` (long critique/breakdown chains, 7
   and 8 reprimes) — these are the "freehand and watch-then-act sessions
   drain's border doesn't reach" that `token-discipline.md`'s general
   session-refresh doctrine is supposed to cover, and that doctrine is
   model-remembered, not structurally enforced. Tracked separately as
   `specs/session-refresh-hook` (new).

Raw reprime-count-per-session breakdown and the pre/post split script are
reproducible from a fresh `agentprof claude --days 7` run; this entry
records the headline numbers, not a re-runnable artifact.
