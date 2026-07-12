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

## Task 05 findings (2026-07-12): the 3a check is skipped, not too loose

Re-ran `agentprof claude --since 2026-07-11T08:07:54Z -o /tmp/postfix.jsonl`
(21,941 samples) and reproduced all three sessions' counts exactly:
`55ae834e` 11 reprimes/$115 (906 calls), `80161f1c` 9/$207 (2,545 calls),
`c2cec1dd` 3/$173 (2,885 calls). Then read each session's actual transcript
under `~/.claude/projects/*/​<session-id>.jsonl`, scanning **assistant-emitted**
`<!-- agentprof:stage=X -->` markers only (grepping the raw file over-counts —
the drain SKILL.md prompt text itself contains the literal marker strings as
instructional text, appearing once per session as loaded content, not as
something the model emitted).

**`55ae834e` — hypothesis (2b) confirmed, cleanly.** This session ran as ONE
unbroken generation from 00:22 to 06:53 (724 lines), recording 9 verdicts
across five specs (tasks-styling, tasks-todoist-migration,
ynab-absorption-gaps, ynab-parity, portfolio-absorption-gaps) before its
first and only baton write, at completion. The `<!-- agentprof:stage=baton-pass
-->` marker was **never emitted once** in the entire transcript — confirmed by
scanning every assistant text block, not just grep-counting substrings (a
naive `grep -c "baton-pass"` returns 40, all from the loaded skill-prompt
text, not actual emissions). A `git commit -m "drain: gen-2 baton checkpoint
— 5 verdicts..."` at verdict 5 (01:42) looked at first like a mid-run baton
pass, but the same session kept dispatching and recording verdicts for
another 5 hours after that commit — it was a bookkeeping checkpoint, not an
actual stop-and-relaunch. The session's own final message ("The run is
complete — 9 verdicts this generation... final baton committed. This session
will not touch the queue again.") confirms the hub itself believed it had
been running as a single generation the whole time — the 3a trigger was
simply never reached. Root cause: SKILL.md step 3's closing line read "Loop
to step 2 while anything is dispatchable," with 3a mentioned only as a
side-note for the degradation override — nothing in the loop-control text
required evaluating 3a's verdict-count trigger before looping back. This is
exactly candidate fix 2b/3 from this task's Goal: "the model simply never
re-checks the condition between wakes."

**`80161f1c` — a different problem (successor-wake latency), not the 3a
trigger.** This session's 3a check DID fire correctly and promptly: inventory
→ one collect-verdict stretch → baton-pass at 02:19, roughly 2 hours and
apparently within budget. But the successor generation's first call didn't
land until 06:23 — a ~4-hour gap — and its first calls after that wake are
exactly the TTL-expiry reprime pattern already documented in this file's
headline measurements (cache falls out of the 5-minute window during a long
await). This session's 9 reprimes are mostly attributable to that wake-gap,
not to the baton trigger failing to fire. Out of scope for this task's fix
(headless-generation dispatch latency is a different mechanism); noted here
so a future session doesn't re-diagnose it as the same bug.

**`c2cec1dd` — not actually a baton-trigger failure at all.** `skill:drain`
frames appear only at turns t04 and t10; all three reprime events happened at
t11–t13, after the drain turn (t10) had already completed and the user had
moved on to unrelated freehand work (a data-generation turn, `/agentic:distill`,
`/exit`). This session's reprime count is real but belongs to failure mode 2
("freehand/non-drain long sessions," already tracked separately) — EVIDENCE.md's
earlier framing of it as a "confirmed skill:drain session" reprime source was
imprecise; the drain portion of that session was clean.

**Fix shipped:** `.claude/skills/drain/SKILL.md` step 3's closing line now
explicitly gates the loop-back — "before doing anything else... evaluate 3a's
relaunch trigger below. Looping back to step 2 without that check first is a
process violation, not a discretionary skip" — and step 3a's opening now
states it is entered "after EVERY recorded verdict (step 3's closing line
sends you here unconditionally)... never only when it happens to feel like a
good moment." No change to the `max(2, 6 − W)` formula itself (2a was not
supported by the transcript evidence) and no change to `reference.md` (its
derivation text was accurate; only the evaluation-frequency instruction in
SKILL.md was broken).

**Re-check needed (MANUAL, unchecked below):** this is a text/discipline fix,
not a structural enforcement mechanism — the model could still skip it,
just with much less textual cover to do so. A follow-up `agentprof claude
--days 7` after a week of drain runs on this fix should confirm the
≥3-reprime share for drain-tagged sessions actually drops; if it doesn't,
the next lever is the task's other candidate — durable per-verdict counter
bookkeeping in `DRAIN-BATON.md` or a mid-run checkpoint file, so the check
no longer depends on the model remembering to run it at all.
