# Task 05: Live re-prime flag on the workboard

Status: done
Depends on: 02
Priority: P2
Budget: 10 turns
Spec: ../SPEC.md (requirement R4)
Touch: agent-console/

## Goal

The workboard needs-attention inbox flags a live session over either
budget arm — `sessions.<id>.reprime_count` ≥ 3 OR `sessions.<id>.p90_ctx`
≥ 250k — joining the live-session scan's session ids exactly against the
summary's `sessions` keys. Live sessions absent from the summary are not
flagged. The flag names the session, which arm tripped, the re-prime
count and cost, and the summary file's mtime (the freshness bound).

## Touch

agent-console only. The summary fields it reads landed in task 02; do NOT
touch `agentprof/`. Cross-spec: `specs/untyped-agent-fanout/tasks/04-*`
also edits agent-console's cost panel and declares a cross-spec
`Depends on:` path to THIS task — one repo-wide drain serializes them
(this one lands first).

## Steps

1. Write the failing renderer tests first, three cases: over-budget live
   session → flag with arm + mtime; under-budget → no flag; live session
   id absent from summary → no flag.
2. Implement in the needs-attention scan path, reading the same summary
   JSON the cost panel already loads (no new endpoint).
3. Handle older summary JSON without `reprime_count` gracefully (treat as
   under-budget on that arm; p90_ctx arm still evaluates).

## Acceptance

- [x] `bash agent-console/scripts/check.sh` → green, including the three new renderer cases — verifier: 154 tests green, tests/test_reprime_flag.py covers over-budget/under-budget/absent-from-summary (evidence/05-workboard-reprime-flag.md)
- [x] `grep -c 'reprime' agent-console/agent-console.py` → ≥ 1 (flag wired into the needs-attention path) — verifier: grep → 12
- [x] Renderer test asserts the mtime appears in the flag line (staleness visible) — verifier: test asserts `ac._dt(MTIME)` in the flag HTML (evidence/05-workboard-reprime-flag.md)

## Decisions

- Live-session source: `_reprime_flags` scans active sessions from `b["repos"][*]["sessions"]` only. Orphan sessions (cwd unresolved) lose their id in `_adapt_board`, so they are not joined against the summary. Reversible: to include orphans, carry their id through `_adapt_board`'s orphan mapping and scan `b["orphans"]` too.
