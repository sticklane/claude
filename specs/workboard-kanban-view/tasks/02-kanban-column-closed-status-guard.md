Status: draft
Discovered-from: specs/workboard-kanban-view/tasks/01-kanban-board-view.md
Spec: ../SPEC.md
Blocking: no

# Guard `_kanban_column` against a future 4th closed status

`_kanban_column` maps closed statuses via `.capitalize()`, which silently
assumes `workboard.CLOSED_TASK_STATUSES` stays a subset of
`{done, deferred, skipped}`. If that set ever grows, the new status would
produce a column name absent from `_KANBAN_COLUMNS` and raise `KeyError`
in `render_workboard_kanban`. Not triggerable with today's constants.

## Acceptance

- [ ] A new unit test named `test_kanban_column_unknown_closed_status`
      exists in `agent-console/tests/test_kanban_view.py` (name absent
      from the repo today, verified 2026-07-19) that simulates
      `workboard.CLOSED_TASK_STATUSES` containing a status outside
      `{done, deferred, skipped}` (e.g. via `unittest.mock.patch`) and
      asserts `_kanban_column` returns a member of `_KANBAN_COLUMNS` —
      the behavior that keeps `render_workboard_kanban`'s
      `buckets[col]` from raising `KeyError`. Behavior, not internals:
      the test must not assert which column the unknown status maps to
      beyond membership, so the worker's fallback choice stays free.
- [ ] `bash agent-console/scripts/check.sh` exits 0 (py_compile, render
      smoke, `unittest discover -s tests` — which picks the new test up
      with no wiring; green today, verified 2026-07-19). Written
      red-first per `.claude/rules/quality-discipline.md`: the guard
      test fails against today's bare `.capitalize()` mapping before
      the fix lands.
