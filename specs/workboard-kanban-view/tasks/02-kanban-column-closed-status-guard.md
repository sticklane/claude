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

<!-- draft: needs runnable criteria before promotion -->
