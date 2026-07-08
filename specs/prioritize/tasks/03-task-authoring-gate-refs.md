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

## Deferred questions

- [2026-07-06 /drain] Criterion 1 greps the *whole* of
  `01-prioritize-scan-script.md` for `bash scripts/check.sh`, but that
  literal string also appears at line 73 inside task 01's `## Discovered`
  note ("Task 01's acceptance criterion 3 names `bash scripts/check.sh`…")
  — the very note that spawned this task — which the worker was told not
  to edit ("nothing else in that file"). Should the fix (a) also make a
  minimal, meaning-preserving edit to line 73 (e.g. drop the `bash ` so it
  reads "names `scripts/check.sh`") so criterion 1's whole-file grep
  passes; or (b) leave line 73 untouched as historical record and treat
  criterion 1 as satisfied by the line-69 fix alone, narrowing criterion
  1's grep to target line 69 only? Blocking: task 03's own DONE verdict —
  criterion 1 currently fails (exit 1) either way until this is resolved.

## Answers

- [2026-07-06] (a) — also edit line 73: drop the `bash ` so it reads
  "names `scripts/check.sh`", preserving the note's meaning while letting
  criterion 1's whole-file grep pass as literally written. Do not narrow
  the grep.
