Status: draft
Priority: P3
Discovered-from: specs/absorb-agent-tools/tasks/05-mutation-guard-repo-divergence.md, specs/absorb-agent-tools/tasks/06-workboard-priority-select-unset.md
Spec: ../SPEC.md
Blocking: no

# agent-console.py and workboard.py have pre-existing formatter drift, inflating future edit diffs

Both `agent-console/agent-console.py` and `.claude/skills/workboard/workboard.py` predate the repo's active PostToolUse formatter hook. In `agent-console.py`: `_adapt_board`'s signature wrapping and mixed f-string quote styles in `render_workboard` don't match the formatter's current output style. In `workboard.py`: an Edit-tool change triggered a full-file reformat (504/296 lines) during task 06, which the verifier flagged as scope creep and the worker had to work around by re-applying via a non-Edit write. Any future edit to either file triggers the hook to reformat these unrelated regions as cosmetic no-ops, inflating that edit's diff with unrelated noise. A one-shot formatter run (e.g. `ruff format`) over each file, in its own commit, would flush the drift once so future edits produce clean diffs again.

## Acceptance

<!-- draft: needs runnable criteria before promotion -->
