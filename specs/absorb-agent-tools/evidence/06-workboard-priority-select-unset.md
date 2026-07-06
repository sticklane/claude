# Verification: 06-workboard-priority-select-unset

Verdict: FAIL

## Acceptance criteria

1. `grep -n 'PRIORITY_RE' .claude/skills/workboard/workboard.py`
   PASS — `225:PRIORITY_RE = re.compile(r"^Priority:\s*\[?(P\d)\]?", re.MULTILINE)`
   plus a use site at line 251.

2. `grep -n '"priority"' agent-console/agent-console.py`
   PASS —
   ```
   622:                    "priority": sp.get("priority", ""),
   771:        f'aria-label="priority">{opts}</select>'
   1217:                prio = _prio_select(sp.get("path", ""), sp.get("priority", ""))
   ```
   Adapter now reads the scanned value; the old hardcoded `""` / "not tracked"
   comment is gone.

3. `cd agent-console && python3 -m pytest tests/test_parsers.py -v`
   PASS — 26 passed, including the two new tests
   `test_spec_priority_flows_from_specmd_to_selected_option` and
   `test_scan_absent_priority_header_defaults_to_unset`.

## Sanity check (independent of test file)

Ran `scan_toolkit_specs` + `_prio_select` directly against two temp SPEC.md
fixtures (not the committed test):
- `Priority: P1` header → `scanned[0]["priority"] == "P1"`,
  `_prio_select` output contains `value="P1" selected`. Confirmed.
- No `Priority:` header → `scanned[0]["priority"] == ""`,
  `_prio_select` output has no `selected` marker anywhere. Confirmed.

Also confirmed TDD red→green: stashing the uncommitted `workboard.py` /
`agent-console.py` changes (leaving only the committed test commit
`84a8e28`) makes both new tests fail with
`KeyError: 'priority'` — i.e. the test was a real, failing-first
reproduction of the bug. Popped the stash afterward to restore the
working tree (no `git checkout`/`git restore` used).

## Append-only task-file check

`git diff 5a32834 -- specs/absorb-agent-tools/tasks/` → **empty output**.
The task file `06-workboard-priority-select-unset.md` has NOT been
touched since the base commit: `Status:` is still `in-progress`, none of
the three acceptance checkboxes are ticked, and no evidence-citation line
was added pointing at this file. This isn't itself an append-only
*violation* (nothing illegal was appended), but per this repo's own
conventions ("Commit on Task Completion", "Record plans... in the task
file") the task file should have been updated to reflect the finished
work and cite this evidence file. Flagging as a process gap.

## Touch-list / scope-creep check

`git diff 5a32834 --stat`:
```
 .claude/skills/workboard/workboard.py | 798 +++++++++++++++++++++-------------
 agent-console/agent-console.py        |   2 +-
 agent-console/tests/test_parsers.py   |  48 ++
 3 files changed, 552 insertions(+), 296 deletions(-)
```

- `agent-console/agent-console.py`: 1 line changed, exactly the adapter fix
  described in Step 3. In scope.
- `agent-console/tests/test_parsers.py`: 48 new lines, the two new tests.
  In scope (declared as the allowed test file).
- `.claude/skills/workboard/workboard.py`: **504 insertions / 296
  deletions** against a 1960-line file. Only a handful of those lines are
  the actual functional change (`PRIORITY_RE` definition, `pm =
  PRIORITY_RE.search(text)`, and threading `"priority": pm.group(1) if pm
  else ""` into the returned spec dict). The remainder is a wholesale
  reformat of the file — collapsing single-line dict/set/tuple literals
  and function-call argument lists into black-style one-arg-per-line
  formatting throughout functions the task never mentions (`find_repos`,
  `git_info`, `_worktree_activity`, `SKIP_DIRS`, etc.), plus stray blank
  line insertions between unrelated functions. This is a scope-creep
  formatting sweep across the whole file, not a "same style as
  STATUS_RE/DEPENDS_RE" minimal patch as Step 1 asked for, and it isn't in
  the task's declared Touch beyond the module named — the Touch line only
  licenses touching this file for the priority feature, not repo-wide
  reformatting. This inflates the diff, makes review harder, and violates
  the CLAUDE.md scope-creep guidance ("formatting sweeps... are scope
  creep even when a repo rule motivates them").

No files outside the declared Touch (+ the named test file) were changed.

## Gates

`cd agent-console && ./scripts/check.sh` -> PASS
```
py_compile: ok
render: ok (57 skills, adapter seam ok)
----------------------------------------------------------------------
Ran 31 tests in 0.179s

OK
check: PASS
```

## Overall verdict: FAIL

Reason: while all three literal acceptance commands pass and the fix is
functionally correct and covered by a real red→green test, the
`workboard.py` diff is dominated by an undeclared, out-of-scope
reformatting sweep (504+/296- lines vs. the ~10 lines the steps describe),
which is scope creep per this repo's own CLAUDE.md guidance. The task file
was also never updated to reflect completion (Status still
`in-progress`, checkboxes unticked, no evidence citation), which is a
process gap on top of the scope-creep finding.
