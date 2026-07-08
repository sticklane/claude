# Verification: Task 03 — Cost panel and refresh endpoint

Verdict: PASS

## Criterion 1 — test suite passes, new tests non-vacuous

Command:
```
cd agent-console && python3 -m unittest discover -s tests -p 'test_*.py' -q
```
Output tail:
```
----------------------------------------------------------------------
Ran 144 tests in 6.936s

OK
```
`tests/test_cost_panel.py` reviewed (195 lines): asserts on rendered HTML
content (`Cost (7d)`, `$4.00`, per-dimension names), top-5 capping (7-entry
fixture, asserts entries 5/6 absent), HTTP status codes (200/403/400), and
JSON payload equality (`{"ok": True, "sessions_added": 7}` / `4`). Not
vacuous — each test has a real assertion tied to fixture data, and the
capping/failure-path tests are genuinely adversarial (would fail against a
naive/no-op implementation).

Result: PASS

## Criterion 2 — render_workboard renders dollar total + top-5 capped rows, ranked by cost

Command: ad-hoc python3 snippet (importlib-loaded `agent-console.py` as `ac`,
built board via `ac._adapt_board(...)`, fed a 7-entry-per-dimension fixture
summary with descending `cost_microusd`).

Result:
```
PASS: render_workboard fixture test with capping+ranking
PASS: missing-summary pending state
IO markers found in render_workboard: []
```
Confirmed: `Cost (7d)` literal present, `$12.35` dollar-formatted total
present (12,345,678 microusd), proj0..proj4/model0..model4/skill0..skill4
present, proj5/6, model5/6, skill5/6 absent (top-5 cap by cost_microusd
descending, verified with non-trivial ranking, not just count).
`inspect.getsource` grep for I/O markers (`open(`, `Path(`, `subprocess`,
`.read(`, `requests.`, `urlopen`) in `render_workboard`'s source found none
— function is pure.

Result: PASS

## Criterion 3 — missing-summary render / handler never 500

Command: ad-hoc python3 snippet patching `ac.get_board` and
`ac._read_cost_summary` to return `None`, constructing `ac.Handler.__new__`,
calling `do_GET()` for `/workboard`.

Output:
```
GET /workboard with missing summary -> code: 200
PASS: never 500, explicit pending shown
```
Body contained "pending" (case-insensitive). Also directly exercised
`render_workboard(board, None)` — no exception, "Cost (7d)" and "pending"
present.

Result: PASS

## Criterion 4 — CSRF-less POST rejected; CSRF'd POST returns sessions_added from written summary

Command: ad-hoc python3 snippet building `Handler.__new__` instances and
calling `do_POST()` for `/api/cost/refresh`.

Output:
```
POST no CSRF -> code: 403
CSRF POST -> code: 200 body: b'{"ok": true, "sessions_added": 7}'
PASS: CSRF flow, sessions_added read from written summary file (not derived)
```
Mocked `ac.subprocess.run` to write a summary JSON with `sessions_added: 7`
to a `_cost_summary_path`-patched temp path; endpoint returned exactly that
value, confirming it is read back from the file, not computed by the
handler. Source review of `refresh_cost()` confirms:
`added = summary.get("sessions_added", 0)` — no independent derivation.

Result: PASS

## Correctness checks

- **Purity of render_workboard**: confirmed via `inspect.getsource` grep —
  no `open(`, `Path(`, `subprocess`, file-read, or network calls in the
  function body. File I/O lives in `_read_cost_summary()` (called from the
  `/workboard` GET handler at agent-console.py:3086), not in
  `render_workboard`. PASS.
- **sessions_added sourced from summary, not derived**: `refresh_cost()`
  (agent-console.py:3028-3049) runs the subprocess, then calls
  `_read_cost_summary()` and reads `summary.get("sessions_added", 0)`.
  do_POST's `/api/cost/refresh` branch (agent-console.py:3233-3248) uses
  the tuple `refresh_cost()` returns unchanged. PASS.
- **Summary JSON shape matches SPEC R3**: `render_workboard` reads
  `cost.get("totals")...get("cost_microusd")` divided by `1_000_000` (plain
  division, agent-console.py:1919-1923), and iterates `by_model`/
  `by_skill`/`by_project` (agent-console.py:1950-1954) each `{name: {...,
  cost_microusd: N}}` — matches SPEC.md R3's pinned shape
  `{by_project,by_skill,by_agent_type,by_model}` each `{name:{sample_type:
  total}}`, `totals{sample_type:total}`, top-level `sessions_added`.
  `by_agent_type` is read (present in test fixture) but not rendered in the
  panel — task's Goal text only requires top-5 rows from
  by_model/by_skill/by_project, which is what's implemented; not a
  discrepancy. PASS.

## Touch discipline

Command:
```
git diff --stat 626854817398bfa9ec6fce85ee131a7cf6caf746 --
```
Output:
```
 agent-console/agent-console.py                     | 385 ++++++++++++++++-----
 agent-console/tests/test_cost_panel.py             | 195 +++++++++++
 .../tasks/03-cost-panel-and-refresh-endpoint.md    |  23 ++
 3 files changed, 513 insertions(+), 90 deletions(-)
```
Only `agent-console/` files and the task's own task file changed. No
`agentprof/` or `refresh-profile.sh` changes. Function-level diff scan
(`grep -E "^[+-]def |^[+-]class "`) shows only the four new/expected
functions (`render_workboard` signature change, `refresh_cost`,
`_read_cost_summary`, `_cost_summary_path`) — no incidental edits to
unrelated functions.

Result: PASS (no scope creep)

## Append-only task-file check

Command:
```
git diff 626854817398bfa9ec6fce85ee131a7cf6caf746 -- specs/workboard-weekly-cost-view/tasks/03-cost-panel-and-refresh-endpoint.md
```
Output: a single hunk adding the `<!-- PLAN (delete on close-out) -->`
comment block (18 lines) after the header fields, before `## Goal`. No
other lines changed — Status line, Touch, Budget, Goal/Steps/Acceptance
text all byte-identical to base. (Note: the Status line in the current file
still reads `in-progress` and none of the acceptance checkboxes are ticked,
despite the implementation existing and passing — this is a documentation
gap the worker should have closed, but it is not a violation of the
append-only rule since nothing was removed or altered improperly; it's
under-filled, not mis-filled.)

Result: PASS (mechanically append-only) — flagged as a minor process note:
Status/checkboxes were never updated to reflect the completed, passing
work.
