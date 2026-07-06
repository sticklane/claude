Status: in-progress
Priority: P1
Discovered-from: specs/prioritize/tasks/01-prioritize-scan-script.md
Spec: ../SPEC.md
Blocking: no

# Task-authoring gate references: point at real per-subproject checks, not scripts/check.sh

Task 01's acceptance criterion 3 (`specs/prioritize/tasks/01-prioritize-scan-script.md:69`) names `bash scripts/check.sh`, but this repo has no top-level `scripts/check.sh` — its canonical checks are per-subproject (`agentprof/scripts/check.sh`, `agent-console/scripts/check.sh`) and the suites in `AGENTS.md`; future task authoring here should point at real gates rather than the global-CLAUDE.md boilerplate path.

Decision (2026-07-06): confirmed — this repo has no top-level `scripts/check.sh` (established convention: task acceptance names real pytest suites; see docs/memory feedback "~/claude has no scripts/check.sh gate"). Fix task 01's acceptance criterion 3 to cite the actual check that was run (the per-subproject suites, e.g. `python3 -m pytest .claude/skills/workboard/ .claude/skills/list-specs/ -q`), and add a one-line authoring note to specs/prioritize/SPEC.md that acceptance criteria in this repo cite real per-subproject checks, never a top-level `bash scripts/check.sh`.

## Acceptance

- [ ] `! grep -q 'bash scripts/check.sh' specs/prioritize/tasks/01-prioritize-scan-script.md` → exits 0 (the boilerplate invocation is gone from task 01's criterion; currently present at line 69)
- [ ] `grep -qi 'per-subproject' specs/prioritize/SPEC.md` → exits 0 (authoring note landed in the spec; currently absent)
