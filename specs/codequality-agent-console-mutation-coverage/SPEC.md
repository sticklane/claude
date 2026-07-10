# agent-console: test the mutation endpoints that currently have none

Status: open

## Problem

agent-console's read paths are well tested (13 test files drive real
`do_GET`/`do_POST` and assert HTML structure), but the highest-risk
surface — the endpoints that mutate sessions, files, and git state — is
the least covered (verified by grep across `agent-console/tests/`,
2026-07-10):

- `resume_agent()` (`agent-console/agent-console.py:2940`) and its route
  `/api/agent/resume` (`agent-console.py:3260`) have **zero** test
  references, while the sibling start/stop mutations are tested
  (`tests/test_parsers.py`, `tests/test_stop_actions.py`).
- `set_priority()` (`agent-console.py:2843`, route `/api/priority` at
  `:3250`) — the wrapper that edits a spec file's `Priority:` header and
  commits — is untested; only the pure `apply_priority` transform is.
- `execute_push()` (`agent-console.py:2362`, registered at `:2441`) is
  never exercised on a success path: existing tests reach it only via
  403-rejection (handler returns before execution) or with
  `subprocess.run` fully mocked, so the dirty-check / commit-message
  assembly (`:2872`) / ahead-behind branching has no coverage.

Secondary coverage gap, same theme: `render_markdown()`'s list/header
parsing (`agent-console.py:1115-1161`) runs on every `/spec/` GET but
nothing asserts its structured output.

## Approach

TDD, per repo conventions, in `agent-console/tests/` (its own
`scripts/check.sh` is the gate; no basename collisions with the toolkit
skill tests as long as runs stay scoped to `agent-console/`):

1. `test_resume_agent.py` (or extend `test_stop_actions.py`): drive
   `POST /api/agent/resume` through the real handler with the process
   boundary (`subprocess`/spawn) mocked at the edge only — assert the
   response JSON and the observable dispatch effect (what command/cwd was
   launched), success and failure (unknown sid, empty prompt) both.
2. set_priority: temp git repo fixture, real `git` (it is local and fast),
   assert the file's `Priority:` header changed and a commit exists —
   behavior, not call order.
3. execute_push success path: temp git repo with a dirty file and a bare
   "remote"; assert commit created and pushed (or, if the network boundary
   must be mocked, assert the assembled git invocations against the dirty /
   clean / ahead cases — one test per branch).
4. render_markdown: parse its HTML output for a fixture doc (headers,
   nested lists, code fences) and assert structure, not exact strings.

## Out of scope

- The hardcoded `127.0.0.1:8901` pprof URL and other constants — filed
  separately in docs/TASKS.md.
- New endpoint behavior; this spec only pins what exists.

## Acceptance criteria

- [ ] `grep -rln "api/agent/resume\|resume_agent" agent-console/tests/`
      is non-empty, and the new tests fail if `resume_agent`'s success
      branch is stubbed to return `(False, "x")` (red-first evidence in
      the task).
- [ ] `grep -rln "set_priority\|execute_push" agent-console/tests/` shows
      direct coverage of both wrappers (not just `apply_priority` /
      registry rejection).
- [ ] `bash agent-console/scripts/check.sh` exits 0.
- [ ] New tests assert observable behavior (response payloads, file/git
      state) — no bare `assert_called_once()`-style assertions without an
      accompanying behavioral check.
