# Verification: Task 03 — workboard reprime line

Verdict: PASS

## Criterion: `bash agent-console/scripts/check.sh` → green including new fixture pair

Command:
```
cd /Users/sjaconette/claude/.claude/worktrees/agent-a9cd3687159a87145/agent-console && bash scripts/check.sh
```
Output tail:
```
py_compile: ok
render: ok (62 skills, adapter seam ok)
----------------------------------------------------------------------
Ran 147 tests in 7.672s

OK
check: PASS
```
Result: ✓ PASS

## Test substance check (not vacuous)

`agent-console/tests/test_cost_panel.py` class `RenderReprimeLine` (lines
138–158):
- `test_reprime_line_rendered_when_section_present`: builds `_REPRIME` fixture
  `{count: 3, cache_write_tokens: 210_000, cost_microusd: 2_540_000,
  by_project: {...}}` (matches task 02's costsummary shape), merges into
  `_SUMMARY`, asserts rendered HTML contains `"3 re-prime"` and `"$2.54"`
  (2,540,000 microusd → $2.54, confirming dollar conversion, not just
  presence).
- `test_reprime_line_absent_when_section_missing`: summary without `reprime`
  key → asserts `"re-prime"` NOT in output, but `"Cost (7d)"` panel still
  present (rest of panel unaffected).
- `test_reprime_section_none_is_omitted_gracefully`: `reprime=None` → renders
  without exception and line omitted.

These assert concrete values (count, dollar string), not just "no error" —
non-vacuous.

## Implementation check

`agent-console/agent-console.py` (~line 1957), inside `render_workboard`:
```python
reprime = cost.get("reprime")
if reprime:
    n = reprime.get("count", 0)
    cost_body += (
        '<div class="sub">Re-prime (7d)</div>'
        f'<div class="line"><span class="trunc">{esc(str(n))} re-primes</span>'
        f'<span class="meta">{_usd(reprime.get("cost_microusd", 0))}</span></div>'
    )
```
Reads `reprime.count` and `reprime.cost_microusd` (matching task 02's shipped
shape `{count, cache_write_tokens, cost_microusd, by_project}`), converts via
existing `_usd` helper (microusd → dollars), falsy/None-safe via `if reprime:`.
Located in agent-console.py's render path, not agentprof.

## Scope check

Command: `git diff --numstat c176481`
```
12  0  agent-console/agent-console.py
33  0  agent-console/tests/test_cost_panel.py
```
Only agent-console/ touched (2 files, both additions). No agentprof/ changes.
Matches Touch: agent-console/. No scope creep found.

## Append-only task-file check

Command: `git diff c176481 -- specs/cache-reprime-visibility/tasks/03-workboard-reprime-line.md`
Output: empty — task file unchanged (Status still reads "in-progress",
acceptance checkbox not yet ticked). This is fine per instructions: close-out
step (flipping Status/checkbox) had not yet occurred at verification time.

## Gates

`scripts/check.sh` is the repo's canonical gate for agent-console and it is
green (py_compile, render smoke test, 147 unit tests including the 3 new
reprime tests).

## Summary

All criterion elements exercised and passing. Tests are substantive (assert
count + dollar value, not just absence of exceptions). Implementation matches
the value contract from task 02. No scope creep. Task file diff is empty
(append-only trivially satisfied, close-out pending).
