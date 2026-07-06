Status: draft
Discovered-from: 01-tool-and-model-durations.md
Spec: ../SPEC.md
Blocking: no

# Document duration_ms in agentprof/SCHEMA.md's well-known metrics table

`agentprof/SCHEMA.md`'s "Well-known metrics" table lists only `wall_ms` →
milliseconds and says "anything else → count". Task 01 mapped `duration_ms`
to milliseconds in `unitFor` (`agentprof/internal/pprofenc/pprofenc.go`),
but the doc table wasn't updated because `SCHEMA.md` is outside task 01's
Touch. Add a `duration_ms` → milliseconds row mirroring how `wall_ms` is
documented.

## Acceptance

<!-- draft: needs runnable criteria before promotion -->
