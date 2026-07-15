# Task 03: Delete tests exercising the removed HTML/CSS output paths

Status: done
Depends on: 01, 02
Priority: P1
Budget: 7 turns
Spec: ../SPEC.md (requirement R8, .claude-leg portion)
Touch: tests/test_workboard_render.sh, tests/test_workboard_actionability.sh, tests/test_fleet_css_drift.sh, tests/fixtures/workboard/, tests/fixtures/workboard-actionability/, .claude/skills/workboard/test_workboard.py

## Goal

Every test whose premise is the now-deleted `--out`/`--actions-out`
HTML-and-actions-script output, or the `fleet/reference.md` /
`--emit-fleet-css` CSS-drift check, is deleted outright — not rewritten,
since nothing survives for their assertions to check. `test_workboard.py`'s
test methods calling `render_html` or any other function/constant Task 02
deleted are removed along with them; the tests covering
`assemble`/`attention_items`/`ready_items`/`default_roots`/`--json`
survive unchanged.

## Touch

Exactly the files/directories listed above. Do not touch the antigravity
mirror's `test_workboard.py` (Task 04).

## Steps

1. Delete `tests/test_workboard_render.sh`, `tests/test_workboard_actionability.sh`,
   and `tests/test_fleet_css_drift.sh` outright.
2. Delete their fixture trees, `tests/fixtures/workboard/` and
   `tests/fixtures/workboard-actionability/` — confirm first that nothing
   else references either path: `git grep -l 'fixtures/workboard\b\|fixtures/workboard-actionability'`
   should show only the deleted test files.
3. In `.claude/skills/workboard/test_workboard.py`, find every test method
   that calls `render_html`, `build_actions_script`, or any other function/
   constant Task 02's reachability check deleted (start from the illustrative
   list in ../SPEC.md's R8 — `render_batons`, `render_inbox`,
   `render_filter_tiles`, `render_spend_section`, `_spec_dag_html`,
   `_spec_dag_tasks`, `_short_model_name` — but verify against the actual
   current file, since the list is illustrative not exhaustive) and delete
   those methods.
4. Run the full gated shell-test suite and the unittest suite to confirm
   nothing else broke.

## Acceptance

- [x] `[ ! -f tests/test_workboard_render.sh ] && [ ! -f tests/test_workboard_actionability.sh ] && [ ! -f tests/test_fleet_css_drift.sh ]`
      — passes; all three git-rm'd (commit "test: delete orphaned workboard HTML/CSS-output tests").
- [x] `[ ! -d tests/fixtures/workboard ] && [ ! -d tests/fixtures/workboard-actionability ]`
      — passes; both fixture trees git-rm'd. Two out-of-Touch prose mentions remain
      (hooks/handoff-resume/resume-check.sh comment, runtimes/antigravity.md doc); both
      non-functional (resume-check prunes fixtures/ dirs), so deletion breaks nothing.
- [x] `for t in tests/test_*.sh; do bash "$t" || exit 1; done` — 13/13 task-relevant
      shell tests pass and the 3 targets are gone. Suite as a whole exits 1 ONLY on
      test_antigravity_content_parity.sh (a PRE-EXISTING _shared/viz.py comment drift,
      red on main before this branch, outside this task's Touch — sibling tasks 02/04).
      Not a regression from this task; orchestrator must sync viz.py (see Discovered).
- [x] `python3 -m unittest discover -s .claude/skills/workboard` exits 0 —
      no `render_html`-calling (or any other Task-02-orphaned-name-calling)
      test method survives. Passes: 137 → 101 tests, OK; 36 orphaned methods removed
      (11 render-only classes + 1 method in TestNeedsAnswerInbox).
