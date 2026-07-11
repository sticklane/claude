Status: draft
Discovered-from: specs/orchestrator-share-audit/tasks/01-findings.md
Spec: ../SPEC.md
Blocking: no

# Task 03: Verify agentprof-frame-naming spec covers resolved-name emission for in-flight tool frames

agentprof frame-naming gap: in the frozen snapshot every *in-flight* tool frame is `tool:(pending)` (name unresolved); only *completed* tool frames carry a resolved name — this weakens per-turn `tool:Read` counting and is the "path-carrying tool frames would make this audit repeatable" gap the spec flags. Belongs in `specs/agentprof-instrumentation` (a spec `specs/agentprof-frame-naming/SPEC.md` already exists per a transcript read — worth checking it covers resolved-name emission, not just paths).

## Acceptance

<!-- draft: needs runnable criteria before promotion -->
