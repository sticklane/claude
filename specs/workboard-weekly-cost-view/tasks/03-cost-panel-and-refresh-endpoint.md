# Task 03: agent-console "Cost (7d)" panel + POST /api/cost/refresh

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers, in every task file — and ## Progress / ## Deferred questions are drain-written sections (single writer, main checkout): workers report that content, never write it. -->

Status: in-progress
Depends on: none
Priority: P2
Budget: 16 turns
Spec: ../SPEC.md (requirements R5, R6, R7)
Touch: agent-console/agent-console.py, agent-console/ (tests)

## Goal

The workboard gains a "Cost (7d)" tile + panel: the `/workboard` HTTP
handler reads `~/.local/state/agentprof/weekly-7d-summary.json` (cheap
small-file read per request, no subprocess) and passes the parsed dict into
`render_workboard` as a new argument; `render_workboard` stays a pure
function (no file I/O) and renders `totals.cost_microusd` as a dollar
string (plain division in Python) plus top-5 rows from
`by_model`/`by_skill`/`by_project`. A missing summary file renders an
explicit empty/pending state with a 200, never a 500. A new CSRF-protected
`POST /api/cost/refresh` (mirroring `/api/profile/refresh`,
`agent-console.py:1544-1577` + route at `:1653`, refs approximate) runs the
refresh synchronously and returns `{"ok": true, "sessions_added": N}`,
reading `sessions_added` back out of the just-written summary JSON — never
deriving it itself.

## Touch

Python/agent-console only — do NOT touch `agentprof/` (tasks 01/02) or
`refresh-profile.sh` (task 04). Build against the summary JSON shape EXACTLY
as pinned in SPEC.md's R3 — this is a cross-task value contract owned by
the spec; if the shape needs to change, stop and surface it rather than
adapting the panel to a stub. Test fixtures use a hand-written summary
JSON matching the pinned shape; real-binary integration is task 04's job.
The refresh endpoint invokes the same refresh step task 04 wires into
`refresh-profile.sh` — until task 04 lands, calling the endpoint against a
missing agentprof `--merge` build may fail at runtime; the endpoint's code
and tests must not depend on task 04 having run (mock/fixture the
subprocess boundary in tests).

## Steps

1. Write the failing tests first (agent-console's existing test
   convention): panel renders dollar totals + top-5 rows from a fixture
   summary dict; missing-file page load → 200 with explicit pending state;
   `POST /api/cost/refresh` without CSRF → rejected, with CSRF → `{"ok":
   true, "sessions_added": N}` where N is read from the (fixture) summary
   file the mocked refresh wrote.
2. Plumb the summary read through the `/workboard` HTTP handler (the same
   place that builds board data via the cached `board()` helper) — never
   from inside `render_workboard` (`agent-console.py:1118`, pure function).
3. Add the tile alongside the existing specs/tasks/active/inbox tiles
   (`agent-console.py:1128-1141`, panel bodies `1147-1175`, refs
   approximate).
4. Add the CSRF-protected route mirroring `/api/profile/refresh`.

## Acceptance

- [ ] agent-console's test suite passes with the new tests (run whatever
      `agent-console/` uses today — locate its existing test invocation
      and extend it; record the exact command as evidence).
- [ ] `python3 - <<'EOF'` (or equivalent unit test) rendering
      `render_workboard` with a fixture summary dict → output contains
      `Cost (7d)`, a `$`-formatted total, and top-5 model/skill/project
      rows (R6).
- [ ] Missing-summary fixture render → 200-path output shows the explicit
      empty/pending state, no exception (R7).
- [ ] CSRF-less `POST /api/cost/refresh` rejected; CSRF'd POST returns
      `{"ok": true, "sessions_added": N}` (R5, subprocess mocked).
