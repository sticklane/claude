Status: pending
Depends on: none
Priority: P3
Budget: 8 turns
Discovered-from: specs/absorb-agent-tools/tasks/05-mutation-guard-repo-divergence.md, specs/absorb-agent-tools/tasks/06-workboard-priority-select-unset.md
Spec: ../SPEC.md
Touch: agent-console/agent-console.py, .claude/skills/workboard/workboard.py
Blocking: no

# agent-console.py and workboard.py have pre-existing formatter drift, inflating future edit diffs

Both `agent-console/agent-console.py` and `.claude/skills/workboard/workboard.py` predate the repo's active PostToolUse formatter hook. In `agent-console.py`: `_adapt_board`'s signature wrapping and mixed f-string quote styles in `render_workboard` don't match the formatter's current output style. In `workboard.py`: an Edit-tool change triggered a full-file reformat (504/296 lines) during task 06, which the verifier flagged as scope creep and the worker had to work around by re-applying via a non-Edit write. Any future edit to either file triggers the hook to reformat these unrelated regions as cosmetic no-ops, inflating that edit's diff with unrelated noise. A one-shot formatter run (e.g. `ruff format`) over each file, in its own commit, would flush the drift once so future edits produce clean diffs again.

## Steps

1. Run the repo's active formatter (e.g. `ruff format`) over `agent-console/agent-console.py` and `.claude/skills/workboard/workboard.py` in isolation — one commit, no other changes riding along.
2. Confirm the diff is formatting-only: no functional/logic changes, verified by running each file's own test suite before and after with identical results.

## Acceptance

- [ ] `git diff --stat` for this commit touches only the two named files
- [ ] `cd agent-console && python3 -m pytest tests/ -v` → same pass count before and after (no behavior change)
- [ ] `bash tests/test_*.sh` (repo-root suites referencing workboard.py, if any) → unchanged pass/fail results before and after
- [ ] A second, unrelated edit to either file (e.g. adding a comment) no longer triggers a full-file reformat — confirmed by making a trivial edit and checking the diff stays scoped to that edit
