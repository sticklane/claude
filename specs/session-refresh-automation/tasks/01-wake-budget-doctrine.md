# Task 01: Wake-budget doctrine in token-discipline

Status: done
Depends on: none
Priority: P1
Budget: 8 turns
Spec: ../SPEC.md (requirement R1)
Touch: .claude/rules/token-discipline.md

## Goal

`.claude/rules/token-discipline.md` carries a "Session refresh" subsection
stating the three R1 points: a main loop that idles past the prompt-cache
TTL is a scheduler, not a thinker (watchers run cheap-tier, judgment goes
to awaited fresh subagents); every autonomous session carries a wake
budget; and the pinned defaults — 3 re-primes or a 250k-token context —
with the 30-day evidence cited from ../SPEC.md, not restated.

## Touch

Only the one rule file. Do NOT touch `.claude/skills/` (task 04 owns the
handoff skill) or anything under `agentprof/` or `agent-console/`.
Cross-spec: `specs/untyped-agent-fanout/tasks/03-*` also edits this file
and declares a cross-spec `Depends on:` path to THIS task, so a single
repo-wide drain serializes them (this one lands first). No action needed
here.

## Steps

1. Read the existing "Cache economics" and "Dispatch authoring" sections
   so the new subsection cites rather than repeats them.
2. Add the "Session refresh" subsection with the literal terms
   "wake budget" and "refresh-over-carry", the pinned defaults, and a
   citation of ../SPEC.md for the 30-day numbers.
3. Keep it under ~30 lines — doctrine, not a manual; drain-specific baton
   behavior stays cited to specs/drain-wake-cost.

## Acceptance

- [x] `grep -ci 'wake budget' .claude/rules/token-discipline.md` → ≥ 1 — returns 1
- [x] `grep -ci 'refresh-over-carry' .claude/rules/token-discipline.md` → ≥ 1 — returns 1
- [x] `grep -c 'session-refresh-automation' .claude/rules/token-discipline.md` → ≥ 1 (evidence cited, not restated) — returns 2
- [x] Manual: a fresh session asked "should a watcher loop run on the
  session model?" answers from the subsection — verified: the "Session
  refresh" subsection's first bullet ("A waiting main loop is a scheduler,
  not a thinker") answers no — watch-then-act pollers run cheap-tier (or
  launchd) and dispatch judgment to awaited fresh subagents, never a
  frontier-tier main loop.
