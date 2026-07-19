Status: draft
Discovered-from: specs/workboard-kanban-view/tasks/01-kanban-board-view.md
Spec: ../SPEC.md
Blocking: no

# Document the new /workboard-kanban route in AGENTS.md

AGENTS.md's "State" section enumerates agent-console's GET routes but
omits the new `/workboard-kanban` route added by task 01. Was outside
task 01's `Touch:`, so left unedited by that unattended worker.

## Acceptance

- [ ] `grep -c 'workboard-kanban' AGENTS.md` ≥ 1 (0 today, verified
      2026-07-19), the mention landing where AGENTS.md describes
      agent-console's views (today that is the Repo map's
      `agent-console/` bullet — note AGENTS.md does not currently
      enumerate GET routes in its State section as this task's body
      assumes; document the board view where the console's other views
      are described rather than inventing a route table).
- [ ] Cross-check the doc against the live surface: `grep -q
    '"/workboard-kanban"' agent-console/agent-console.py` still
      matches the route handler (present today, verified 2026-07-19) —
      the documented path must be the served path, not a paraphrase.

Depth ceiling: prose-only doc edit — L0 is the honest ceiling. The
behavioral complement is the verifier judgment instruction: confirm the
AGENTS.md sentence accurately describes what
`render_workboard_kanban` serves at `/workboard-kanban` (read both, no
paraphrase drift), plus `/prose-review` on the edited AGENTS.md prose
per CLAUDE.md's authoring conventions.
