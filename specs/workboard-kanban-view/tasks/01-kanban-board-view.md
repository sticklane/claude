# Task 01: Kanban board view for the workboard dashboard

Status: done
Depends on: none
Priority: P2
Budget: 18 turns
Spec: ../SPEC.md (requirements R1-R9)
Touch: agent-console/agent-console.py, agent-console/tests/test_kanban_view.py

## Goal

`agent-console/agent-console.py` gains a new read-only `GET /workboard-kanban`
route rendering the same scanned repo/spec/task data the existing
`/workboard` route uses, but grouped into seven fixed status columns
(Pending, In Progress, Needs Verification, Blocked, Done, Deferred,
Skipped) instead of a flat per-repo list. A new "Board" nav tab links to
it. The existing `/workboard` list view is unchanged.

## Touch

This task touches only `agent-console/agent-console.py` (new function,
new route wiring, new CSS block, nav tab edit) and a new test file
`agent-console/tests/test_kanban_view.py`. It must not modify
`render_workboard()`, `_adapt_board()`, `_dag_tasks()`, or
`.claude/skills/workboard/workboard.py` — this task only reads/reuses
their existing output, per the spec's Solution section.

## Steps

1. Write a failing test in `agent-console/tests/test_kanban_view.py`
   (mirror `agent-console/tests/test_parsers.py`'s
   `importlib.util.spec_from_file_location` loading pattern — the module
   filename is hyphenated and not directly `import`-able) asserting
   `_kanban_column(status)` returns the correct column name for one
   representative status per bucket: `open`→`Pending`, `claimed`→`In
Progress`, `needs_verification`→`Needs Verification`,
   `waiting`→`Blocked` (catch-all), `done`→`Done`, `deferred`→`Deferred`,
   `skipped`→`Skipped`. Confirm it fails (`_kanban_column` doesn't exist
   yet).

2. In `agent-console.py`, add `_kanban_column(status: str) -> str`
   (SPEC.md R2) near `_dag_tasks`/`_adapt_board` (agent-console.py:578-677).
   Import/reuse `workboard.OPEN_TASK_STATUSES` and
   `workboard.CLOSED_TASK_STATUSES` for the open/closed membership check —
   do not duplicate the literal string sets. Run the test from step 1;
   confirm it now passes.

3. Add `render_workboard_kanban(b: dict) -> str`, taking the same board
   dict `render_workboard(b)` already consumes (from `get_board()`). It
   must (SPEC.md R1-R6):
   - Flatten every repo's every spec's `tasks` list into one list of
     cards, each tagged with that spec's `repo` name, `slug`, `id`, and
     `priority`.
   - Bucket each card into one of the seven columns via `_kanban_column`.
   - Render all seven columns, always, left to right, in this exact
     order: Pending, In Progress, Needs Verification, Blocked, Done,
     Deferred, Skipped — even when a column has zero cards.
   - Each column header renders its label and card count as two distinct
     text nodes (e.g. `<span class="col-head">Pending</span><span
class="count">12</span>`), never concatenated into one text run.
   - Done/Deferred/Skipped columns wrap their cards in a `<details>`
     element (collapsed by default — no `open` attribute), with the
     `col-head`-wrapped label inside `<summary>`. Pending/In
     Progress/Needs Verification/Blocked columns render expanded, with
     the `col-head` label in a plain heading element, not inside
     `<details>`.
   - Each card shows: the task title linked to `/spec/{id}` (the spec
     `id` already present in the reused data — do NOT link to
     `/task/{id}`, that data isn't available here), a `repo:spec-slug`
     badge, and the spec's `priority` if non-empty. Cards do not show
     `unblock` step text (out of scope).
   - Every card carries a `data-text` attribute:
     `(repo + spec-slug + task-title)` lowercased.

4. Wire `GET /workboard-kanban` into the request dispatch table
   (agent-console.py:3287-3312), alongside the existing `/workboard`
   branch: call `get_board()` then `render_workboard_kanban(...)`, wrapped
   in `page("board", readout, body, with_filter=True)` the same way
   `/workboard`'s handler wraps `render_workboard`.

5. Add a third tab, "Board", to `page()`'s `<nav class="tabs">`
   (agent-console.py:1904), linking to `/workboard-kanban`, using the
   existing `tab()` helper so it active-highlights the same way the
   Skills/Workboard tabs do.

6. Add CSS for the board layout to the `CSS` constant
   (agent-console.py:1614-1789): a `.kanban-board` flex row of
   `.kanban-column`s, `.col-head` label styling, and `.kanban-card`
   styling — reuse existing color/spacing custom properties already
   defined in `CSS` rather than introducing new ones.

7. Run `agent-console/scripts/check.sh` (byte-compiles, smoke-tests
   `render_skills`/`render_workboard` via a fixture, runs
   `python3 -m unittest discover -s tests`) and fix anything it flags.

## Acceptance

- [x] `agent-console/scripts/check.sh` → `check: PASS` (198 tests incl. new
      `test_kanban_view.py`; render smoke ok — existing `/workboard` intact)
- [x] `grep -c "workboard-kanban" agent-console/agent-console.py` → 2 (≥1)
- [x] `grep -c "render_workboard_kanban" agent-console/agent-console.py` → 2 (≥1)
- [x] R2 importlib `_kanban_column` mapping command → prints `ok`
- [x] `curl .../workboard-kanban` → HTTP 200; anchored col-head grep emits
      the seven labels once each in order Pending, In Progress, Needs
      Verification, Blocked, Done, Deferred, Skipped (served from worktree on
      port 8898 — launchd 8899 runs the pre-merge main checkout)
- [x] `grep -c 'data-text=' /tmp/kb.html` → 5 (> 0)
- [x] `grep -c 'href="/spec/' /tmp/kb.html` → 5 (> 0)
- [x] `grep -c '<details' /tmp/kb.html` → 3 (≥3; columns line-isolated)
- [x] `curl .../ | grep -c 'href="/workboard-kanban"'` → 1 (≥1)
- [x] `curl -X POST .../workboard-kanban` → 403 (non-2xx; Host/CSRF guard)
- [x] End-to-end: Board tab renders `class="tab on"` (active); all 7 columns
      present, Done/Deferred/Skipped in `<details>` with no `open` attr
      (collapsed); Pending=87, In Progress=1 cards. Filter equivalence: every
      card carries `data-text`; PAGE_JS:1843 toggles `.hidden` on all
      `[data-text]` unchanged, so a repo token narrows across all columns.
      Live browser click-through not exercised — extension lacked
      site-permission for 127.0.0.1:8898 this session (verified via
      HTTP/DOM-source instead).
