# Task 05: Live re-prime flag on the workboard

Status: in-progress
Depends on: 02
Priority: P2
Budget: 10 turns
Spec: ../SPEC.md (requirement R4)
Touch: agent-console/

<!-- PLAN (build)
Seam: render_workboard(b, cost) is the only place with BOTH live sessions
(b["repos"][*]["sessions"], state=="active", carrying "sid") and the parsed
summary. Add mtime as a 3rd param so the flag line can show the freshness bound.
Files/order (agent-console/ only):
1. tests/test_reprime_flag.py — 3+ cases: over-budget→flag w/ arm+mtime;
   under-budget→no flag; live id absent from summary→no flag; context arm
   still fires when reprime_count missing (Step 3). RED first.
2. agent-console.py:
   - constants REPRIME_BUDGET=3, CTX_BUDGET=250_000.
   - _reprime_flags(board, summary, summary_mtime)->list[inbox-item dict]:
     join active repo-session sids EXACTLY against summary["sessions"] keys;
     per over-budget session emit item naming session+arm(s)+count+cost+mtime.
     Absent from summary => skipped. Missing reprime_count => 0 (ctx arm still
     evaluates). Uses _dt(mtime) for the stamp.
   - render_workboard(b, cost=None, summary_mtime=None): inbox_items =
     list(b["inbox"]) + _reprime_flags(...); use inbox_items in tile count,
     readout, and the inbox block (was b["inbox"]).
   - _cost_summary_mtime()->float|None; do_GET /workboard passes it through.
What could go wrong: mutating b (keep pure — build local list); orphan
sessions lose id in _adapt_board (use active repo sessions only — reversible).
-->

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

- [ ] `bash agent-console/scripts/check.sh` → green, including the three new renderer cases
- [ ] `grep -c 'reprime' agent-console/agent-console.py` → ≥ 1 (flag wired into the needs-attention path)
- [ ] Renderer test asserts the mtime appears in the flag line (staleness visible)
