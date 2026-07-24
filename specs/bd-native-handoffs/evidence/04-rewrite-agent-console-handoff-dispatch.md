# Verification: task 04 — rewrite agent-console handoff dispatch

Verdict: PASS

Base commit for diff: fb3efe64. Worktree: agent-a65c67e711f63a6b0, branch drain/md-d8f63486.

## Step 0 — empty-diff pre-check

`git add -A && git diff --cached --stat fb3efe64` is non-empty (agent-console.py,
3 test files, and the task file itself all changed). Proceeded to full verification.

## Per-criterion evidence

1. ✓ `grep -c "HANDOFF" agent-console/agent-console.py` → `0`. Confirmed the
   retired `HANDOFF.md`-era references are gone.

2. ✓ `cd agent-console && python3 -m pytest tests/test_dispatch_kinds.py -k ResumeHandoff -q`
   → `3 passed, 11 deselected in 0.01s`.

3. ✓ `cd agent-console && python3 -m pytest tests/test_drilldown_registry.py tests/test_parsers.py -q`
   → `38 passed in 0.20s`.

4. ✓ `grep -c 'h\["path"\]\|h\.get("path")\|\["mtime"\]' agent-console/agent-console.py`
   → `3`. All three residual matches inspected line-by-line and confirmed
   unrelated to handoffs:
   - line 870: `open_spec_list.sort(key=lambda s: s["mtime"], reverse=True)` — spec list mtime.
   - line 2496: `_ago(sp["mtime"])` — spec row rendering.
   - line 2526: `_ago(t["mtime"])` — task-summary rendering.
   No `h["path"]`, `h.get("path")`, or `h["mtime"]`/handoff `["mtime"]` read
   remains anywhere in the file. `_adapt_board` (line 827-838) now projects
   exactly `{id, title, tracked_ids, updated_ts}` from `r["handoffs"]`;
   `build_entity_registry` (939-978) drops the handoff loop entirely (its
   docstring now states "Handoffs are bd issues with no file of their own,
   so they register nothing here"); `_scanner_dispatch_prompts` (1099-1119)
   keys resume prompts by `(name, issue_id)` via `h.get("id")`;
   `build_action_registry`'s handoff loop (1237-1247) dispatches on
   `h.get("id")`/`h.get("title")` through `_handoff_target(path, issue_id)`;
   `_handoff_meta` (2233-2238) renders `h['id']`/`h.get("tracked_ids")`/
   `h['updated_ts']`. All bd-native fields, no retired-shape reads.

## Forcing-test genuineness check

`test_scanner_shaped_handoff_yields_resume` (test_dispatch_kinds.py:202-215)
builds its handoff record via `_handoffs_from_workboard()`, which patches
`workboard._open_handoff_issues` and calls the REAL `workboard.scan_handoffs()`
— not a hand-copied fixture — then asserts `"path"`/`"mtime"` are absent from
the record and that `build_action_registry` still produces a correct
`dispatch-resume-handoff` entry.

Reverted-code check: extracted `agent-console.py` at base commit fb3efe64,
ran the equivalent scenario (a real `scan_handoffs()`-shaped handoff record,
git-root repo path) through the OLD `build_action_registry`. Result:
`resumes found: 0` — `(r,) = resumes` raises
`ValueError: not enough values to unpack (expected 1, got 0)`, because the old
code's `h.get("path") or ""` yields `""` for a bd-shaped record (no `path`
key), so `if hpath and prompt:` never fires and no dispatch is registered.
The new test is therefore genuinely forcing — it fails against the
unmodified base code, not just a contrived break.

## Task-file append-only check

`git diff fb3efe64 -- specs/bd-native-handoffs/tasks/04-rewrite-agent-console-handoff-dispatch.md`
shows exactly two changes: the `Status:` header (`pending` → `in-progress`)
and an inserted `<!-- PLAN (delete at close-out) ... -->` comment block.
No Goal/Steps/Acceptance text was altered. Compliant.

## Standard gate

`cd agent-console && ./scripts/check.sh` → `py_compile: ok`, `render: ok
(93 skills, adapter seam ok)`, `Ran 219 tests in 7.874s`, `OK`, `check: PASS`.

## Scope-creep finding

`agent-console/tests/test_drilldown_filter.py` was modified but is NOT in
the task's `Touch:` list (`agent-console/agent-console.py,
agent-console/tests/test_dispatch_kinds.py,
agent-console/tests/test_drilldown_registry.py,
agent-console/tests/test_parsers.py`). The diff there is a single fixture
update: the old `{"title": ..., "path": "handoffs/h.md", "mtime": 0}` handoff
dict is replaced with the bd-native shape
`{"id": "md-4c1a", "title": ..., "tracked_ids": [], "updated_ts": 0}`. This
is not a convention-driven edit (no version bump/formatting sweep) — it is a
mechanical, minimal fix required to keep this pre-existing, untouched-by-Touch
test passing after `_adapt_board`'s field-shape change (the old fixture would
raise `KeyError: 'id'` in `_adapt_board` otherwise, confirmed by that
function's dict-literal projection at agent-console.py:827-835). Flagging as
a Touch-list omission rather than a blocking scope-creep violation, since the
edit is a single hardcoded-value swap with no added functionality, and
`check.sh`'s full 219-test run stays green.

## Criteria adequacy (R6, R7)

The requirement — `agent-console.py`'s handoff-dispatch consumers use task
03's bd-issue-shaped fields instead of the retired `path`/`title`/`mtime`
shape — is entailed at **L2 (behavior)**: criteria 2-4 exercise real function
calls (`build_action_registry`, `_scanner_dispatch_prompts`,
`_adapt_board` via `test_drilldown_registry.py`) against handoff records
produced by the actual `workboard.scan_handoffs()` output shape (criterion 4's
forcing test), not just string literals. Criterion 1 alone is L0
(text-presence), but it is one of four criteria, not the sole evidence for
the requirement. No depth-ceiling annotation is present in this task's
Acceptance section, so the ladder binds informationally; the aggregate
evidence across all four criteria clears L2 and is adequate — not INCOMPLETE.
