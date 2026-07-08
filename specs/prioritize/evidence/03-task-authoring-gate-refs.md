# Verification: 03-task-authoring-gate-refs

Verdict: PASS (acceptance criteria + line-73 binding requirement + append-only check all satisfied). One process finding: task 03's own file was never updated to reflect completion (Status still `in-progress`, both acceptance checkboxes still `[ ]`, no evidence citations added to task 03's `## Acceptance` — see Finding below).

## Criterion 1

Command: `! grep -q 'bash scripts/check.sh' specs/prioritize/tasks/01-prioritize-scan-script.md`
Result: exit 0 → PASS
Evidence: task 01 line 69 was rewritten from
`- [x] \`bash scripts/check.sh\` → green — repo has no top-level ...`
to
`- [x] \`python3 -m pytest .claude/skills/workboard/ .claude/skills/list-specs/ -q\` (the real per-subproject check; repo has no top-level \`scripts/check.sh\`, ...)`
No occurrence of the literal string `bash scripts/check.sh` remains anywhere in the file (confirmed via the whole-file grep, which also covers the `## Discovered` note at line 73 — see below).

## Criterion 2

Command: `grep -qi 'per-subproject' specs/prioritize/SPEC.md`
Result: exit 0 → PASS
Evidence: SPEC.md gained a new `## Authoring note` section (inserted before `## Open questions`):
```
## Authoring note

Acceptance criteria in this repo cite the real per-subproject checks that
were actually run (e.g. `python3 -m pytest .claude/skills/workboard/ -q`),
never a top-level `bash scripts/check.sh` — this repo has no such gate.
```

## Line-73 binding requirement (task's `## Answers`)

Command: `nl -ba specs/prioritize/tasks/01-prioritize-scan-script.md | sed -n '68,76p'`
Line 73 now reads:
`- Task 01's acceptance criterion 3 names \`scripts/check.sh\`, but this repo has no top-level \`scripts/check.sh\` — its canonical checks are per-subproject (\`agentprof/scripts/check.sh\`, \`agent-console/scripts/check.sh\`) and the suites in \`AGENTS.md\`; future task authoring here should point at real gates rather than the global-CLAUDE.md boilerplate path.`

Diff vs. base (358e6c7) for this line: only the `bash ` prefix was dropped before the first backticked `scripts/check.sh`; every other word is byte-identical. Meaning is preserved — the note still correctly explains why criterion 3 (now fixed) referenced the wrong gate. Matches the `## Answers` instruction exactly: "(a) — also edit line 73: drop the `bash ` so it reads 'names `scripts/check.sh`', preserving the note's meaning ... Do not narrow the grep." → PASS.

## Append-only check on task 03's own file

Command: `git diff 358e6c7 -- specs/prioritize/tasks/03-task-authoring-gate-refs.md`
Result: empty diff (no output).

Base commit `358e6c7` ("drain: task 03 (prioritize) in-progress") is also the current `HEAD` of this worktree — i.e., no commits were made on top of it, and the working tree's copy of `03-task-authoring-gate-refs.md` is byte-identical to that commit. Mechanically this passes "append-only" (there are zero non-whitelisted edits, because there are zero edits of any kind), but it also means the worker never flipped task 03's own `Status:` header to `done`, never ticked either `## Acceptance` checkbox in task 03's own file, and never added evidence-citation lines there — all the actual fix work landed in task 01's file and SPEC.md instead (both still uncommitted: `git status --short` shows `M specs/prioritize/SPEC.md` and `M specs/prioritize/tasks/01-prioritize-scan-script.md`).

FINDING (process, not a criterion failure): task 03's own task file was left in `in-progress` / unchecked state despite the underlying acceptance criteria now passing. This should be flaged to the orchestrator — task 03 is functionally done but its own bookkeeping (Status line, checkboxes, evidence pointers) was not updated, and none of the three fix commits have been made yet (SPEC.md and task 01 changes are uncommitted in the worktree).

## Scope check

Only `specs/prioritize/SPEC.md` and `specs/prioritize/tasks/01-prioritize-scan-script.md` were modified (per `git status --short`). Both are within the task's intended scope (SPEC.md authoring note + task 01's criterion/note fix per the task's own `## Answers`). No edits to unrelated files. Task 03's own file is untouched (see above finding — arguably it *should* have been touched to record completion, but that is an omission, not scope creep).
