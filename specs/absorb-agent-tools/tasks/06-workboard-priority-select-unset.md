Status: draft
Priority: P0
Discovered-from: specs/absorb-agent-tools/tasks/02-import-agent-console-deduped.md
Spec: ../SPEC.md
Blocking: no

# Workboard per-spec Priority select always shows unset

`render_workboard`'s per-spec `Priority:` `<select>` will always show unset, since `workboard.py`'s scan doesn't extract a spec's `Priority:` header at all (only per-task status/deps) — a cosmetic regression from the data-source swap, not fixable within the adapter alone.

## Acceptance

<!-- draft: needs runnable criteria before promotion -->
