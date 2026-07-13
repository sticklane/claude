# Verification: Task 02 — import agent-console, deduped

Verdict: PASS

Base commit: 608cfdbf0791bbec0000afdad5abacd9df95b0d9 (current HEAD; only commit).
Work is uncommitted; `agent-console/` is a new untracked directory (`git status --porcelain` → `?? agent-console/`). Nothing else in the repo is modified.

## Acceptance criteria (run literally as written)

1. `bash agent-console/scripts/check.sh` → exit 0
   ```
   py_compile: ok
   render: ok (37 skills, adapter seam ok)
   ----------------------------------------------------------------------
   Ran 22 tests in 0.178s

   OK
   check: PASS
   ```
   ✓ PASS (exit 0)

2. `test ! -f agent-console/viz.py && test ! -d agent-console/.claude` → exit 0
   ✓ PASS (exit 0) — no vendored viz.py, no nested .claude/

3. `grep -cE "viz-sha256|--self-sha256" agent-console/scripts/check.sh` → 0
   ✓ PASS — output `0`

4. `grep -cE "def (scan_specs|scan_tasks|scan_handoffs|build_board)" agent-console/agent-console.py` → 0
   ✓ PASS — output `0`

5. `grep -n "workboard" agent-console/agent-console.py | grep -c "import"` → ≥1
   ✓ PASS — output `1`

6. `python3 .claude/skills/workboard/workboard.py --json > /dev/null && python3 .claude/skills/workboard/workboard.py --out /tmp/wb-contract.html && test -s /tmp/wb-contract.html` → exit 0
   ✓ PASS — exit 0, `/tmp/wb-contract.html` populated ("10 repos · 21 open specs · 90 open tasks · 6 active sessions · 17 need attention")

7. `git diff --stat main -- .claude/skills/` → empty
   ✓ PASS — no output (skill tree untouched)

8. `grep -rn "sjaconette\|Jaconette" agent-console/ | wc -l` → 0
   ✓ PASS — output `0`

9. `find agent-console -name "*.plist" ! -name "*.tmpl" | wc -l` → 0
   ✓ PASS — output `0` (only `launchd/agent-console.plist.tmpl` present)

## Independent sanity checks

1. **Module resolution not vendored.** `agent-console/agent-console.py` lines 40–60:
   `_skills_root()` derives `<repo>/.claude/skills` from `Path(__file__).resolve().parent.parent`
   (with `AGENT_CONSOLE_SKILLS_ROOT` env override), then:
   ```python
   viz = _load_module("viz", SKILLS_ROOT / "_shared" / "viz.py")
   workboard = _load_module("workboard", SKILLS_ROOT / "workboard" / "workboard.py")
   ```
   Confirmed these resolve to `.claude/skills/_shared/viz.py` and `.claude/skills/workboard/workboard.py` relative to the server's own file location — not vendored copies (criterion 2 above independently confirms no `viz.py` file exists in `agent-console/`).

2. **`/workboard` route wiring.** `do_GET` (line ~1531-1532):
   ```python
   elif path == "/workboard":
       self._send(render_workboard(get_board()).encode("utf-8"))
   ```
   `get_board()` (line ~703) calls `workboard.assemble(workboard.default_roots(), max_depth=3, stale_days=STALE_DAYS, quiet=True)` and pipes the result through `_adapt_board()` before returning — not any deleted scanner function. `build_board`/`scan_specs`/`scan_tasks`/`scan_handoffs` do not exist in the file (confirmed via criterion 4's grep).

3. **`render_workboard` unmodified.** Extracted `render_workboard` (through end of function, next top-level `def`) from both the migrated copy and `~/agent-console/agent-console.py` (the pre-migration source) and diffed them byte-for-byte:
   ```
   diff orig_render_workboard.py new_render_workboard.py
   ```
   → empty diff, exit 0. Both are 260 lines, byte-identical. Only the adapter (`_adapt_board`) and its input (`assemble()` output) changed, exactly as the task requires.

4. **`scripts/check.sh` smoke test genuinely exercises the adapter seam.** Read the script: it builds an `assemble()`-shaped fixture dict (`repos`/`orphan_sessions`/`inbox`/`liveness_unknown` keys matching workboard's real output shape), calls `m._adapt_board(fixture, [], [])`, feeds the result into `m.render_workboard(board)`, and asserts `"fixture-repo" in board_html`. This is the adapter path, not the old `build_board()/render_workboard(model)` call (which no longer exists in the file). Ran fresh: exits 0, "adapter seam ok" printed.

5. **`tests/test_parsers.py` clean of deleted functions, still green.**
   ```
   grep -nE "scan_specs|scan_tasks|scan_handoffs|build_board|_status_of|_parse_task|_priority_of|_priority_rank|parse_session_entries|_session_start_ts|collect_sessions" agent-console/tests/test_parsers.py
   ```
   → no matches (grep exit 1 / empty). Ran `python3 -m unittest discover -s tests -v`: 22 tests, all pass, 0.178s, including a new `TestAdaptBoard.test_adapts_repos_specs_sessions_and_inbox` test covering the adapter.

## Gates

- `bash agent-console/scripts/check.sh` — the repo's own canonical check for this subtree — passes (py_compile + render smoke + 22 unit tests). No repo-root `scripts/check.sh` exists / is in scope (Touch is `agent-console/` only).

## Scope-creep check

- `git status --porcelain` shows only `?? agent-console/` — no tracked file anywhere else in the repo was modified.
- `git diff 608cfdbf0791bbec0000afdad5abacd9df95b0d9 -- 'specs/absorb-agent-tools/tasks/*.md'` → empty diff. Task file itself untouched (Status line still reads `in-progress`; worker did not tick acceptance boxes or update Status — a process gap, not a correctness failure, since I verified every criterion directly).
- `git diff --stat main -- .claude/skills/` → empty (criterion 7), confirming no skill-tree edits as required by Touch.
- `.claude-plugin/**`, `AGENTS.md`, `antigravity/**` at repo root: untouched (not present in `git status`).
- `agent-console/__pycache__/` and `tests/__pycache__/` exist on disk but are gitignored (`agent-console/.gitignore` lists `__pycache__/` and `*.pyc`) and untracked — not scope creep since they'd never be committed.

## Verdict

PASS — all 9 acceptance checkboxes pass verbatim; all 5 independent sanity checks confirm correct, non-overfitted implementation (import resolution, route wiring, byte-identical `render_workboard`, genuine adapter-seam smoke test, and clean/green `test_parsers.py`). No scope creep detected.
