Status: draft
Priority: P1
Discovered-from: specs/prioritize/tasks/01-prioritize-scan-script.md
Spec: ../SPEC.md
Blocking: no

# Task-authoring gate references: point at real per-subproject checks, not scripts/check.sh

Task 01's acceptance criterion 3 (`specs/prioritize/tasks/01-prioritize-scan-script.md:69`) names `bash scripts/check.sh`, but this repo has no top-level `scripts/check.sh` — its canonical checks are per-subproject (`agentprof/scripts/check.sh`, `agent-console/scripts/check.sh`) and the suites in `AGENTS.md`; future task authoring here should point at real gates rather than the global-CLAUDE.md boilerplate path.

## Acceptance

<!-- draft: needs runnable criteria before promotion -->
