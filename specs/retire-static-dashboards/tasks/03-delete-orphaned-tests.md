# Task 03: Delete tests exercising the removed HTML/CSS output paths

Status: pending
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

- [ ] `[ ! -f tests/test_workboard_render.sh ] && [ ! -f tests/test_workboard_actionability.sh ] && [ ! -f tests/test_fleet_css_drift.sh ]`
- [ ] `[ ! -d tests/fixtures/workboard ] && [ ! -d tests/fixtures/workboard-actionability ]`
- [ ] `for t in tests/test_*.sh; do bash "$t" || exit 1; done` exits 0.
- [ ] `python3 -m unittest discover -s .claude/skills/workboard` exits 0 —
      no `render_html`-calling (or any other Task-02-orphaned-name-calling)
      test method survives.
