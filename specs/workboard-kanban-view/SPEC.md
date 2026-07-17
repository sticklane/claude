# Kanban board view for the workboard dashboard

Breakdown-ready: true

## Problem

The live agent-console dashboard's `/workboard` route (`agent-console/agent-console.py`)
renders open work as a flat per-repo list with `<details>` collapsibles
(`render_workboard()`, agent-console.py:2063-2491). There is no way to see,
at a glance, how many tasks sit in each pipeline stage across all repos —
answering "what's in progress right now" or "what's blocked" requires
expanding every repo's collapsible and scanning task-by-task. The scanner
(`.claude/skills/workboard/workboard.py`) already computes a clean status
vocabulary per task (`Status:` header parsing, workboard.py:245-264); this
spec adds a second view that renders that same scanned data as status
columns instead of a per-repo list.

## Solution

Add a new `/workboard-kanban` route and `render_workboard_kanban()` function
to `agent-console/agent-console.py`, reusing the exact same board-scan call
`render_workboard()` already uses (no new scanner invocation, no new data
source). The route renders one column per canonicalized task status,
flattening every open spec's `tasks` list across all repos into cards
tagged with their parent repo/spec. A new "Board" nav tab is added to the
shared `page()` shell (agent-console.py:1874-1911) alongside the existing
Skills/Workboard tabs — this is purely additive; the existing list view is
untouched.

The view is read-only (no drag, no write route), matching the read-only
contract in `docs/agent-dashboards.md:122` and the workboard skill doc.
Grouping is filter-only, not swimlanes: cards from all repos render in one
flat board, and the existing free-text filter (`#q` input, already wired in
`PAGE_JS` to toggle `.hidden` on any `[data-text]` element — agent-console.py:1798-1800)
is reused as-is to narrow by repo or spec name. No new JS is required for
filtering: each card just needs a `data-text` attribute, the same
convention already used elsewhere on the page.

Column status values are canonicalized by reusing workboard.py's own
`OPEN_TASK_STATUSES` / `CLOSED_TASK_STATUSES` sets (workboard.py:245-258)
rather than re-deriving the bucketing logic — any status literal outside
both sets (e.g. `blocked`, `waiting`, `failed`, `draft`) is workboard.py's
existing catch-all and renders in a single "Blocked" column.

## Requirements

R1. A new `GET /workboard-kanban` route renders a kanban board via a new
`render_workboard_kanban()` function, called from the same request
dispatch table as the existing `/workboard` route
(agent-console.py:3287-3312). It reuses the same board-data scan
`render_workboard()` calls today — no second scan invocation, no new
scanner entry point. Because that data passes through `_dag_tasks()`
(agent-console.py:578-603), which silently drops any task file whose name
doesn't start with a numeric `NN-` prefix, the board inherits the same
filter: a non-`NN-`-prefixed task file will not appear as a card. This
is existing behavior of the reused data, not a gap introduced by this
spec, and is not worth a workaround (see Out of scope).

R2. Task statuses are canonicalized into columns as follows:

- `pending`, `open`, `todo`, `ready` → **Pending**
- `in-progress`, `in_progress`, `claimed` → **In Progress**
- `needs-verification`, `needs_verification` → **Needs Verification**
- any status string not in workboard.py's `OPEN_TASK_STATUSES` or
  `CLOSED_TASK_STATUSES` → **Blocked**
- `done` → **Done**
- `deferred` → **Deferred**
- `skipped` → **Skipped**

Import/reuse workboard.py's `OPEN_TASK_STATUSES` and
`CLOSED_TASK_STATUSES` constants for the open/closed membership check
rather than duplicating the literal string sets. Implement the mapping as
a named, independently callable pure function, `_kanban_column(status: str) -> str`,
taking a raw status string and returning one of the seven column labels
above — not inlined into the render function — so the mapping itself is
directly testable without rendering HTML.

R3. Columns render left to right in this fixed pipeline order: Pending,
In Progress, Needs Verification, Blocked, Done, Deferred, Skipped. All
seven columns always render, in this order, regardless of how many cards
each holds — a status with zero current tasks still renders its (empty)
column and header rather than being omitted.

R4. Each task renders as one card showing: the task title linked to the
parent spec's detail page at `/spec/{id}`, using the spec `id` field
`_adapt_board()` already computes (agent-console.py:650,
`_entity_id("spec", ...)`) — not a per-task `/task/{id}` link, since the
adapted board data this view reuses (`_dag_tasks()`, agent-console.py:578-603)
does not carry a task's absolute path, only `_adapt_board`'s spec-level
entries do. Each card also shows a `repo:spec-slug` badge and the parent
spec's `priority` field if non-empty. Cards do not show the task's
`unblock` step text — that field is on a separate spec-level
`blocked_tasks` list (agent-console.py:666-674), not on the per-task
entries this view flattens, and joining the two is out of scope (see Out
of scope).

R5. Every column header renders its label and card count as two distinct
text nodes — e.g. the label wrapped in an element carrying a `col-head`
class, with the count in a sibling element — never concatenated into one
text run (e.g. not `Pending (12)` as a single node). This holds for all
seven columns, not just the closed ones, because the acceptance checks
below anchor on the `col-head`-wrapped label text. The three
closed-status columns (Done, Deferred, Skipped) additionally render
collapsed by default behind a `<details>` element, using the same
collapsible pattern already used for repo blocks in `render_workboard()`
(agent-console.py:2404) — the `col-head`-wrapped label lives inside that
`<details>`'s `<summary>`. Pending, In Progress, Needs Verification, and
Blocked columns render expanded by default, with the `col-head` label in
a plain heading element (not inside a `<details>`).

R6. Every card carries a `data-text` attribute containing
`repo + spec-slug + task-title`, lowercased — the same attribute
convention the existing `#q` filter already reads
(agent-console.py:1798-1800) — so the free-text filter narrows kanban
cards with no new JS.

R7. `page()`'s `<nav class="tabs">` (agent-console.py:1904) gains a third
tab, "Board", linking to `/workboard-kanban`, active-highlighted via
the same `tab()` helper and `active` parameter the existing two tabs
use.

R8. The board view adds no POST/write route and no drag/drop handlers.
Observing the board never mutates task or spec state.

R9. The board page uses the existing 25s auto-refresh JS already present
in `PAGE_JS` (agent-console.py:1849) — no new polling logic.

## Out of scope

- Drag-to-change-status or any other mutation of task `Status:` headers
  from the board (R8 forbids it outright).
- Swimlanes by repo or by spec — filtering via the existing `#q` input is
  the only grouping mechanism (R6).
- A dedicated repo-dropdown filter control — the existing free-text filter
  covers repo/spec narrowing (see Solution); adding a second filter widget
  is unnecessary duplication.
- Folding inbox states (`blocked`/`needs-review`/`stale`, which apply at
  the repo/spec level, not per-task) into the board's columns — the board
  is scoped to per-task `Status:` values only.
- Any new storage/coordination layer (SQLite, Dolt, or otherwise). This is
  a UI-only rendering of already-scanned data; `docs/task-tracking-design-research-2026-07.md`'s
  storage-layer conclusion is out of scope here and is not reopened by
  this spec.
- Replacing `/workboard`'s existing list view — the board is a new,
  additive tab (R7).
- Archival, pagination, or expiry of old Done/Deferred/Skipped cards
  beyond the default-collapsed disclosure in R5.
- Showing a Blocked card's `unblock` step text — that data lives on the
  spec-level `blocked_tasks` list, not the per-task entries this view
  flattens (R4), and joining the two is deferred to a future spec.
- Working around `_dag_tasks`'s existing `NN-`-prefix filter (R1) so
  non-`NN-`-prefixed task files show up as cards — this view inherits
  whatever `render_workboard()`'s data already includes or excludes.

## Acceptance criteria

Verified against current on-disk state (`agent-console/agent-console.py`,
3505 lines) on 2026-07-16: `workboard-kanban` and `render_workboard_kanban`
both grep-count 0 today, so the criteria below are not vacuous.

- [ ] `grep -c "workboard-kanban" agent-console/agent-console.py` → ≥1
      (route path literal; 0 today, verified 2026-07-16)
- [ ] `grep -c "render_workboard_kanban" agent-console/agent-console.py` → ≥1
      (new render function defined; 0 today, verified 2026-07-16)
- [ ] `agent-console.py` has a hyphenated filename, so it's not `import`-able
      directly — `agent-console/tests/test_parsers.py:14` and its siblings
      already load it via `importlib.util.spec_from_file_location`; the
      check for R2 follows the same pattern:
      `python3 -c "import importlib.util as u; s=u.spec_from_file_location('ac','agent-console/agent-console.py'); m=u.module_from_spec(s); s.loader.exec_module(m); k=m._kanban_column; assert k('open')=='Pending'; assert k('claimed')=='In Progress'; assert k('needs_verification')=='Needs Verification'; assert k('waiting')=='Blocked'; assert k('done')=='Done'; assert k('deferred')=='Deferred'; assert k('skipped')=='Skipped'; print('ok')"`
      → prints `ok` (covers R2's status→column mapping directly, independent
      of HTML rendering)
- [ ] With the server running locally (`python3 agent-console/agent-console.py &`
      or via the existing launchd job), `curl -fsS http://127.0.0.1:8899/workboard-kanban -o /tmp/kb.html`
      returns HTTP 200 and contains all seven column headers, anchored to
      the `col-head` class so a card titled e.g. "Done" can't produce a
      false match: `grep -o 'col-head[^>]*>Pending<\|col-head[^>]*>In Progress<\|col-head[^>]*>Needs Verification<\|col-head[^>]*>Blocked<\|col-head[^>]*>Done<\|col-head[^>]*>Deferred<\|col-head[^>]*>Skipped<' /tmp/kb.html | wc -l`
      → 7 (covers R2's rendering, R5's label/count text-node split)
- [ ] Column order is left-to-right per R3: the same anchored grep run with
      `-o` (no `wc -l`) emits the seven labels in exactly that sequence
      (covers R3, including that all seven render even if some are empty)
- [ ] `grep -c 'data-text=' /tmp/kb.html` → > 0, given the repo currently
      has 156 open tasks (covers R6)
- [ ] `grep -c 'href="/spec/' /tmp/kb.html` → > 0 (covers R4's card-to-spec link)
- [ ] `grep -c '<details' /tmp/kb.html` → ≥3, one per closed-status column
      (Done, Deferred, Skipped) (covers R5's default-collapsed disclosure)
- [ ] `curl -fsS http://127.0.0.1:8899/ | grep -c 'href="/workboard-kanban"'`
      → ≥1, confirming the nav tab renders on every page via the shared
      `page()` shell (covers R7)
- [ ] `curl -fsS http://127.0.0.1:8899/workboard-kanban -X POST -o /dev/null -w '%{http_code}'`
      → non-2xx (the server 404s unknown POST paths via `do_POST`'s handler
      lookup, agent-console.py:3474; confirms no write route was added — covers R8)
- [ ] End-to-end: open `http://127.0.0.1:8899/workboard-kanban` in a browser,
      confirm the Board tab is highlighted active, columns render side by
      side with visible cards in at least Pending/In Progress, and typing a
      known repo name (e.g. "fooszone") into the filter box hides cards
      from other repos across all columns.

## Open questions

(none)

## Parallelization

Single task (all requirements are tightly coupled to one new function and
its call site — splitting would create artificial cross-task coordination
on the same HTML/CSS class contract). No concurrent-safe groups; Task 01
runs solo.
