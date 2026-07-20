Run-token: b74f9fc1664dd9db
Generation: 2
Spec: specs/drain-frontier-scanner
Breakdown-failed:
Intake-failed:
Stub-intake-failed:

## Done / next

- Task 01 done and merged (drain_frontier.py scanner, 22 unit tests, the
  basic-window golden fixture).
- Next: task 02 (drain consumes scanner, depends on 01, done — P1) and
  task 03 (eval trajectory assert, no deps — P2) are both dispatchable.
  This spec's window is empty (0 in-flight) and its Parallelization
  section groups 02+03 (`- Group: 02, 03`) — with the default W=1 for
  this spec only one runs at a time; tie-break picks 02 (P1 over P2).
  Task 04 (mirrors + manifest bump) depends on 01+02, not yet
  dispatchable.

## Anomalies

- None. No parked/zombie tasks in this spec this generation.
