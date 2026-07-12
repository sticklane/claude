Status: obsolete
Closed: 2026-07-12 — stub-intake gate-confirmed OBSOLETE. The frame-naming requirement (resolved `tool:<name>` leaf for completed tool_use/tool_result pairs; explicit `tool:(pending)` leaf for in-flight unresolved calls) is already pinned by specs/agentprof-instrumentation/SPEC.md R1 (lines 152-156) and R2 (lines 157-160), so a separate frame-naming-check is redundant. The stub's referenced specs/agentprof-frame-naming/SPEC.md does not exist (confirmed via find).
Discovered-from: specs/orchestrator-share-audit/tasks/01-findings.md
Spec: ../SPEC.md
Blocking: no

# Task 03: Verify agentprof-frame-naming spec covers resolved-name emission for in-flight tool frames

agentprof frame-naming gap: in the frozen snapshot every *in-flight* tool frame is `tool:(pending)` (name unresolved); only *completed* tool frames carry a resolved name — this weakens per-turn `tool:Read` counting and is the "path-carrying tool frames would make this audit repeatable" gap the spec flags. Belongs in `specs/agentprof-instrumentation` (a spec `specs/agentprof-frame-naming/SPEC.md` already exists per a transcript read — worth checking it covers resolved-name emission, not just paths).

## Acceptance

<!-- draft: needs runnable criteria before promotion -->
