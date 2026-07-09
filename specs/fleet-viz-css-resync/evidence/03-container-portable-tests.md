# Verification: 03-container-portable-tests

Verdict: PASS

Environment: verified as root (`id -u` → `0`) in this GNU/Linux container,
as the task requires.

## Acceptance criteria

1. `bash tests/test_drain_owner_protocol.sh` → exit 0
   - Ran directly. Output: `pass: 15 fail: 0`. Exit code 0. ✓

2. `bash tests/test_hook_templates.sh` → exit 0
   - Ran directly. Output: `pass: 77, fail: 0`. Exit code 0. ✓

3. `bash tests/test_install_gates.sh` → exit 0
   - Ran directly. Output: `pass: 159 fail: 0`. Exit code 0. ✓

4. `for t in tests/test_*.sh; do bash "$t" || { echo "FAIL: $t"; exit 1; }; done` → exit 0
   - Ran full sweep across all `tests/test_*.sh`. No `FAIL:` line printed;
     loop exit code 0. No regressions in other test files. ✓

5. Evidence cites each added skip (if any) with its reason
   - No skip was added. The root path (`id -u -eq 0`) replaces the
     chmod-000 fixture with a broken symlink (`ln -s
"$REPO/scripts/no-such-target" "$REPO/scripts/check.sh"`), which
     still exercises an assertion (exit 0 + exactly one stderr warning),
     not a skip. Confirmed by reading `templates/stop-gate.sh`: the guard
     is `if [ ! -f "$check" ] || [ ! -r "$check" ]; then` — a broken
     symlink makes `-f` false (broken symlinks fail `-f`, which follows
     the link), so the SAME fail-open branch fires for root as chmod 000
     fires for non-root. ✓

## Diff review (git diff 230802d -- tests/)

- `tests/test_drain_owner_protocol.sh`: added a `sedi()` helper (sed →
  temp file → `cat` back) and replaced all 3 `sed -i '' EXPR file`
  (BSD-only syntax) call sites with `sedi EXPR file`. Substitution
  expressions and target files are unchanged — same 3 replacements
  performed, just through a portable path. Assertion count unchanged
  (15 before, 15 after via `assert` grep count).

- `tests/test_install_gates.sh`: added `sedi()` (same pattern) and a
  `filemode()` helper (`stat -c '%a'` GNU, `stat -f '%Lp'` BSD
  fallback). Replaced `stat -f '%Lp' "$PY_CHECK"` with `filemode
"$PY_CHECK"` — the assertion still does `assert_eq "python fixture:
check.sh mode 755" 755 "$(filemode "$PY_CHECK")"`, i.e. still compares
  to `755`, unchanged. Replaced the R3-marker `sed -i ''` call with
  `sedi`, same substitution expression. Assertion count unchanged (157
  before, 157 after).

- `tests/test_hook_templates.sh`: the chmod-000 "unreadable" block was
  replaced with a uid-branching block:
  - root (`id -u -eq 0`): removes `check.sh` and symlinks it to a
    nonexistent target (`scripts/no-such-target`) — unresolvable for
    every user including root, so DAC bypass cannot make it "readable".
  - non-root: unchanged `chmod 000`, still covering the `-r` guard.
    Both branches run the same two assertions afterward:
    `assert_eq "stop-gate exits 0 when check.sh is unusable" 0 "$RH_EXIT"`
    and `assert_eq "unusable check.sh warns with one stderr line" 1
"$(stderr_line_count)"` — exit-0 and exactly-one-stderr-line are both
    still asserted, matching the pre-change semantics (previously "is
    unreadable" / "unreadable check.sh warns"; renamed, not weakened).
    After the assertions, the block explicitly rebuilds a working,
    executable `check.sh` for the subsequent R13 cases (not present
    before, but necessary since the file is now removed rather than just
    chmod'd, and does not affect the assertions above it). Assertion count
    unchanged (56 before, 56 after).
    No assertion in any file was deleted, and no assertion is silently
    skipped for root — the root branch runs a real, different fixture that
    reaches the same guarded code path.

## Task-file append-only check

`git diff 230802d -- specs/fleet-viz-css-resync/tasks/03-container-portable-tests.md`
shows only a 16-line addition: the `<!-- PLAN (delete at close-out): ... -->`
comment block above `## Goal`. No edits to Goal/Steps/Touch/Budget/Acceptance
text. This is within the allowed "plan comment block" maintenance category.

Note (not a criterion failure, but worth flagging): the `Status:` header
is still `in-progress` and none of the 5 acceptance checkboxes were ticked
by the worker, despite the commit `e266f2d` containing the passing fix.
Per the task's own append-only note, ticking boxes / flipping Status /
citing evidence is allowed but was not done — the task file does not
self-report completion. This does not affect the PASS verdict on the
runnable acceptance criteria (all 4 commands independently verified
above), but the orchestrator should be aware the task file's own status
line understates progress.

## Gates / scope creep

`git diff 230802d --stat` touches exactly the 3 files listed in `Touch:`
plus the task file's own plan-block (which is exempt). No scope creep.

## Overfitting check

The `sedi`/`filemode` helpers are generic (parameterized by expression/
file, not hardcoded to specific test strings) and the root-branch fixture
targets the actual `[ ! -f ... ] || [ ! -r ... ]` guard in
`templates/stop-gate.sh`, not a special-cased shortcut for the test
harness. Confirmed by reading `templates/stop-gate.sh` line 51.
