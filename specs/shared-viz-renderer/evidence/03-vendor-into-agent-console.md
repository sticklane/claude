# Evidence: 03-vendor-into-agent-console

Verifier: agentic:verifier, base commit 1cf9e9d, one commit 38614ba on
`task/03-vendor-viz` (agent-console repo, worktree), verdict PASS.

- `bash scripts/check.sh` → exit 0, `check: PASS` (py_compile, conformance ×2,
  render smoke test, 33 unit tests incl. new `TestSessionStartTs`).
- Tamper test: appended a byte to `viz.py` → `conformance: FAIL (viz.py
  diverged from ~/claude/.claude/skills/_shared/viz.py)`, exit 1; restored →
  `diff` empty, sha256 identical (`abc9fc3e...`), rerun → `check: PASS`.
- `grep -c '_dep_graph_svg\|_task_stroke' agent-console.py` → `0`.
- Wiring confirmed: `import viz`; `viz.dag(sp.get("tasks", []))` at the former
  DAG call site; `viz.timeline(rows)` replacing the flat-text Sessions block;
  `viz.VIZ_CSS` injected into `<style>` ahead of the host `CSS`.
- `start_ts` resolution (`_session_start_ts`) implements the spec order:
  earliest transcript-record timestamp → transcript file's `st_birthtime` →
  passed-in fallback; `parse_session_entries` sets it from each entry's
  `fullPath`; the PID-injected live-session merge branch in
  `_build_board_locked` sets `start_ts = lr["last"] or now` (transcript-less
  case, per spec bucket 3).
- `scripts/check.sh` conformance step matches R8: primary toolkit-diff
  hard-fails when `~/claude` is present; secondary body-sha256-vs-header
  hard-fails independent of toolkit presence; toolkit-absent path prints the
  exact `conformance: SKIPPED (toolkit source not present — corruption-check
  only)` line and passes.
- End-to-end render sanity check (`/workboard` via a temporary local server):
  `viz-bar`=8, `viz-lane`=3, `viz-graphwrap`=20, `viz-node`=116 in the
  rendered HTML — sessions render as a timeline, specs render DAGs, both via
  `viz.py`.
- Scope check (verifier): `git diff 1cf9e9d 38614ba --stat` touches exactly
  `agent-console.py`, `scripts/check.sh`, `viz.py` (the task's Touch list)
  plus `tests/test_parsers.py` (new-behavior test coverage) — no extraneous
  files.
