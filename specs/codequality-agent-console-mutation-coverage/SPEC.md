# agent-console: test the mutation endpoints that currently have none

Status: open

## Problem

agent-console's read paths are well tested (13 test files drive real
`do_GET`/`do_POST` and assert HTML structure), but the highest-risk
surface — the endpoints that mutate sessions, files, and git state — is
the least covered (verified by grep across `agent-console/tests/`,
2026-07-10). **Line numbers below are snapshots, not a contract** —
`agent-console.py` has drifted between every critique round on this spec
so far; find each function by name (`def resume_agent`, `def
set_priority`, `def execute_push`, `def render_markdown`) at
implementation time rather than trusting a stale number.

- `resume_agent()` (`agent-console/agent-console.py:3134`) and its route
  `/api/agent/resume` (`agent-console.py:3465`) have **zero** test
  references, while the sibling start/stop mutations are tested
  (`tests/test_parsers.py`, `tests/test_stop_actions.py`).
- `set_priority()` (`agent-console.py:3037`, route `/api/priority` at
  `:3455`) — the wrapper that edits a spec file's `Priority:` header and
  commits — is untested; only the pure `apply_priority` transform is.
- `execute_push()` (`agent-console.py:2554`, dispatched via the `"push"`
  action-kind table at `:2633`) is never exercised on a success path:
  existing tests reach it only via 403-rejection (handler returns before
  execution) or with `subprocess.run` fully mocked. Its real branches are
  `subprocess.TimeoutExpired` → `exit:None`; `returncode==0` →
  `_invalidate_board()` + `ok:true`; `returncode!=0` → `ok:false` with the
  exit code — no dirty-check or ahead/behind logic exists, none of these
  branches have coverage.

Secondary coverage gap, same theme: `render_markdown()`'s list/header
parsing (`agent-console.py:1211-1256`) runs on every `/spec/` GET but
nothing asserts its structured output.

## Approach

TDD, per repo conventions, in `agent-console/tests/` (its own
`scripts/check.sh` is the gate; no basename collisions with the toolkit
skill tests as long as runs stay scoped to `agent-console/`):

1. `test_resume_agent.py` (or extend `test_stop_actions.py`): drive
   `POST /api/agent/resume` through the real handler with the process
   boundary (`subprocess`/spawn) mocked at the edge only — assert the
   response JSON and the observable dispatch effect (what command/cwd was
   launched). Cover both real failure branches of `resume_agent()`
   (agent-console.py:3134): unknown sid → `(False, "not a known session")`,
   and `_claude_run_bg` raising `OSError`/`RuntimeError` (e.g. `claude` not
   on PATH) → `(False, str(e))`. An empty/whitespace prompt is NOT a
   failure — `resume_agent` defaults it to `"continue"` and succeeds; do
   not test it as one.
2. set_priority: temp git repo fixture, real `git` (it is local and fast),
   assert the file's `Priority:` header changed and a commit exists —
   behavior, not call order.
3. execute_push: drive `execute_push(action)` directly (agent-console.py:2554)
   with `action["argv"]` pointed at a real git push against a bare "remote" —
   no dirty-check or ahead/behind logic exists, so cover exactly its three
   branches: (a) rc 0 → response `ok:true`, `exit:0`, and the board cache
   invalidated (`_invalidate_board`/`_board_cache["ts"]` reset, verified via
   a stale-then-fresh `_board_cache["ts"]` read, not a mock-called-once
   check); (b) rc non-zero (e.g. push to an unreachable/rejecting remote) →
   `ok:false`, `exit:<code>`, message contains the exit code; (c)
   `subprocess.TimeoutExpired` (mock `subprocess.run` to raise it) →
   `exit:None`, message states the timeout.
4. render_markdown: parse its HTML output for a fixture doc (headers, lists,
   code fences) and assert structure, not exact strings.

## Out of scope

- The hardcoded `127.0.0.1:8901` pprof URL and other constants — filed
  separately in docs/TASKS.md.
- New endpoint behavior; this spec only pins what exists.

## Acceptance criteria

- [ ] `grep -rln "api/agent/resume\|resume_agent" agent-console/tests/`
      is non-empty, and the new tests fail if `resume_agent`'s success
      branch is stubbed to return `(False, "x")` (red-first evidence in
      the task).
- [ ] `grep -rln "set_priority" agent-console/tests/` is non-empty and
      shows direct coverage of the wrapper (not just `apply_priority` /
      registry rejection).
- [ ] `grep -rln "execute_push" agent-console/tests/` is non-empty and
      shows direct coverage of the wrapper's rc-0/rc-nonzero/timeout
      branches (not just registry rejection with `subprocess.run` fully
      mocked).
- [ ] `grep -rln "render_markdown" agent-console/tests/` is non-empty, and
      the new tests fail if heading-level parsing is stubbed to always
      emit `<h1>` (e.g. `level = len(heading.group(1))` replaced with
      `level = 1`) — a concrete mutation-kill bar for the parser, not a
      reviewer judgment call.
- [ ] All new tests are `unittest.TestCase` subclasses (`agent-console`'s
      `scripts/check.sh` runs `python3 -m unittest discover`, which does
      not collect bare pytest-style `def test_...` functions).
- [ ] `bash agent-console/scripts/check.sh` exits 0.
- [ ] New tests assert observable behavior (response payloads, file/git
      state) — no bare `assert_called_once()`-style assertions without an
      accompanying behavioral check.
