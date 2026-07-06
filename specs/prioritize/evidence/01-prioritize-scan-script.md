# Verification: 01-prioritize-scan-script

Verified in worktree `/Users/sjaconette/claude/.claude/worktrees/task-01-prioritize-scan-script`
(branch `task/01-prioritize-scan-script`), base commit
`06e6e3d39f5df80706edc1902b24dc958240c131`.

## Verdict: PASS

## Criteria

1. **Unit tests** — ✓
   Command: `python3 -m pytest .claude/skills/prioritize/test_prioritize_scan.py -q`
   Output: `13 passed in 0.11s`

2. **CLI table output** — ✓ (adjusted per instructions: run from worktree root, not
   `/Users/sjaconette/claude`, since the file only exists on this branch)
   Command: `python3 .claude/skills/prioritize/prioritize_scan.py` (cwd = worktree root)
   Output (head):
   ```
   | Ref | Title | Status | Priority |
   | --- | --- | --- | --- |
   | absorb-agent-tools/04-attended-closeout.md | ... | pending | P2 |
   | drain-sweep-preservation/01-snapshot-before-sweep.md | ... | pending | P0 |
   | drain-sweep-preservation/02-environment-kill-halt.md | ... | pending | P1 |
   | drain-sweep-preservation/03-worker-commits-and-bump.md | ... | pending | P2 |
   | prioritize/02-skill-md-mirror-bump.md | ... | pending | P2 |
   | skill-profiling-workboard/05-attended-install-and-e2e.md | ... | pending | P2 |
   ```
   Header matches exactly `Ref | Title | Status | Priority`; only
   pending/blocked/deferred rows present; no `archive/` refs; not empty so no
   "nothing to reprioritize" case exercised live, but that path is covered by
   unit + subprocess tests (`test_empty_rows_render_nothing_to_reprioritize`,
   `test_zero_qualifying_prints_nothing_to_reprioritize`).

3. **`scripts/check.sh` gate** — N/A, absent; equivalent gates green.
   Confirmed absence: `ls scripts/` → `ls: scripts/: No such file or directory`
   (no top-level `scripts/` directory at all in this repo).
   Equivalent: `python3 -m pytest .claude/skills/workboard/ .claude/skills/list-specs/ -q`
   → `87 passed in 0.44s` (importlib reuse did not break neighbors).

## Requirements re-check (SPEC.md R1/R2) via test file inspection

Read `.claude/skills/prioritize/test_prioritize_scan.py` in full (222 lines).
Tests build real fixture trees under `tempfile.TemporaryDirectory()` and
assert parsed structure (via a local `parse_rows` markdown-table parser), not
whole-string matches:

- `test_only_pending_blocked_deferred_are_collected` — exercises all excluded
  statuses (`done`, `skipped`, `in-progress`, `in_progress`, `claimed`,
  `draft`, `failed`) plus the three qualifying ones in one fixture; asserts
  the resulting status set is exactly `{blocked, deferred, pending}`. Genuine
  structural check, not overfit to one input.
- `test_ref_is_slug_slash_filename` — `Ref == "<slug>/<filename>"`.
- `test_rows_sorted_by_spec_slug_then_task_number` — mixed-order fixture
  (`zeta` before `alpha`, `10-late` before `02-early`), asserts final sorted
  order.
- `test_task_with_priority_header_shows_that_value` / `..._without...` — P0
  header vs. `P2 (default)` fallback.
- `test_headerless_task_counts_as_pending_and_is_listed` — no `Status:` line
  → scanner default `pending`, row still listed.
- `test_archive_specs_are_excluded` — `specs/archive/old-one` task excluded
  even though otherwise qualifying.
- `CliSubprocessTestCase.test_this_repo_runs_clean_and_excludes_archive` runs
  the real script as a subprocess against this actual repo root (found via
  `.git`-marker walk, mirroring `list_specs`' pattern) and asserts
  `"archive/"` not in stdout — a real end-to-end check, not just against
  fixtures.

All match the acceptance list's stated coverage (zero-qualifying case,
mixed-status filtering, Ref format, sort order, priority default/override,
header-less-as-pending, archive exclusion). No test appears to special-case
exact literal strings beyond the fixed protocol strings ("nothing to
reprioritize", table header cells) which are the contract itself, not
overfitting.

## Touch / scope-creep check

`git status --short` in the worktree: only
`?? .claude/skills/prioritize/prioritize_scan.py` (untracked — see Defect
below). No other paths modified.

`git diff 06e6e3d39f5df80706edc1902b24dc958240c131 --stat`:
```
 .claude/skills/prioritize/test_prioritize_scan.py | 222 ++++++++++++++++++++++
 1 file changed, 222 insertions(+)
```
Confirms `.claude/skills/workboard/workboard.py` and everything under
`.claude/skills/list-specs/` are untouched relative to base. No scope creep.

## Append-only task-file check

`git diff 06e6e3d39f5df80706edc1902b24dc958240c131 -- specs/` → **empty**
(no output at all). The task file `specs/prioritize/tasks/01-prioritize-scan-script.md`
is byte-identical to the base commit: `Status:` still reads `in-progress`,
acceptance checkboxes are still unchecked `[ ]`, no evidence-citation lines
were added. This is trivially "no disallowed changes" (nothing changed at
all), but flagged as a process defect below since the work is otherwise
complete and green.

## Defects / findings (not criteria failures, but worth flagging)

- **Uncommitted work**: `prioritize_scan.py` (the actual implementation) is
  untracked in the worktree — never `git add`/committed. Only the test file
  (in commit `0383502`, "red" step) is committed. Per repo/user conventions
  ("never leave finished work uncommitted", TDD green/refactor steps each
  committed), the green-step commit for `prioritize_scan.py` is missing.
- **Task-file bookkeeping not updated**: `Status:` line is still
  `in-progress` and acceptance checkboxes are still unticked despite the
  work passing all three criteria live. No evidence-citation lines were
  added to the task file per the append-only convention. This means the
  task file's own record disagrees with the actual (passing) state.

Neither defect is one of the three literal acceptance commands, so they do
not change the PASS verdict on criteria 1–3, but they represent unfinished
process — the task should not be marked "done" until these are addressed.
