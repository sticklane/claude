Status: draft
Priority: P3
Discovered-from: specs/absorb-agent-tools/tasks/05-mutation-guard-repo-divergence.md
Spec: ../SPEC.md
Blocking: no

# agent-console.py has pre-existing formatter drift, inflating future edit diffs

`agent-console/agent-console.py` predates the repo's active PostToolUse formatter hook. Two regions (`_adapt_board`'s signature wrapping, and mixed f-string quote styles in `render_workboard`) don't match the formatter's current output style — any future edit to the file triggers the hook to reformat these unrelated regions as cosmetic no-ops, inflating that edit's diff with unrelated noise. A one-shot formatter run (e.g. `ruff format agent-console/agent-console.py`) over the whole file would flush the drift once, so future edits produce clean diffs again.

## Acceptance

<!-- draft: needs runnable criteria before promotion -->
