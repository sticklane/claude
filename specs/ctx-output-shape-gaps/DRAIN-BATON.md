Run-token: 213b64b2b9be6090
Generation: 2
Spec: specs/ctx-output-shape-gaps
Breakdown-failed:
Intake-failed:
Stub-intake-failed:

## Done / next

See `specs/ctx-dispatch-adoption/DRAIN-BATON.md` (same run, same
Run-token, written in the same commit) for the full generation-1 summary
— this run is a no-argument (whole `specs/` queue) launch holding 2
spec leases simultaneously (swarm mode), so both baton files carry the
same log to avoid a successor missing either.

**Next for this spec specifically:**
`ctx-output-shape-gaps/tasks/02-tree-files-mode.md` (P2) was admitted in
generation 1's admission pass but never dispatched — the verdict budget
(5 verdicts at W=1) ran out on `ctx-dispatch-adoption` tasks first.
Dispatch it next. `tasks/03-skill-docs-rows.md` is still BLOCKED
(`Unblock:` line — read it fresh, don't assume generation 1's snapshot
still holds).

## Anomalies

See `specs/ctx-dispatch-adoption/DRAIN-BATON.md`'s Anomalies section —
identical for this run.
