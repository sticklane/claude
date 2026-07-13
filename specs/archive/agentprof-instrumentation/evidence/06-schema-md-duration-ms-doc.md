# Verification: 06-schema-md-duration-ms-doc

Verdict: PASS (with scope-creep finding — see below)

## Criteria

1. `cd agentprof && grep -n 'duration_ms' SCHEMA.md | grep -q 'millisecond'`
   ✓ PASS — exit 0. Line 51: `| \`duration_ms\` | \`milliseconds\` |`

2. `cd agentprof && grep -n 'duration_ms' README.md | grep -q 'millisecond'`
   ✓ PASS — exit 0. Line 294: `  \`duration_ms\` → \`milliseconds\`, \`calls\` → \`count\`; unknown metric names get`

3. `cd agentprof && bash scripts/check.sh`
   ✓ PASS — exit 0. Output:
   ```
   check: format-check ok
   check: lint ok
   check: tests ok
   ```

## Semantic correctness

- SCHEMA.md's "Well-known metrics" table now has a `duration_ms` row placed
  directly after `wall_ms`, both mapping to `milliseconds`, matching the
  existing `wall_ms` row's formatting exactly.
- README.md's inline unit list ("Well-known units: ...") now includes
  `duration_ms` → `milliseconds` alongside the existing `wall_ms` →
  `milliseconds` entry.
- Matches `agentprof/internal/pprofenc/pprofenc.go`'s `unitFor` (lines
  17-28): `case metric == "wall_ms", metric == "duration_ms": return
"milliseconds"` — SCHEMA.md/README.md now correctly document both
  metrics mapping to the same unit.

## Append-only task-file check

`git diff a2e1972d10bb07e631e5cccd7f94291b24746ff6 -- specs/agentprof-instrumentation/tasks/06-schema-md-duration-ms-doc.md`
→ empty (no changes). Task file is unmodified from base at verification
time — Status still reads `in-progress`, acceptance checkboxes unticked.
Not a violation; worker had not yet updated Status/checkboxes when this
verification ran.

## Scope-creep finding

`git diff a2e1972d10bb07e631e5cccd7f94291b24746ff6 -- agentprof/SCHEMA.md agentprof/README.md`
shows changes well beyond the single `duration_ms` row/entry required by
the task's Steps:

- SCHEMA.md and README.md's embedded JSON example blocks were reformatted
  from compact/hand-wrapped style to fully expanded, one-key-per-line JSON
  (`"values": {...}` and `"labels": {...}` blocks).
- README.md's "Commands" markdown table was fully realigned/repadded
  (column widths changed throughout, unrelated to duration_ms).
- SCHEMA.md's "Well-known metrics" table header separator row was
  repadded (`|-----------------|` → `| --------------- |`).

These are formatting-sweep changes, almost certainly produced by
`scripts/check.sh`'s `format-check` step (a markdown/prettier formatter)
auto-fixing the files after the single-line edit was made, rather than
being deliberate task work. The task's Steps only call for adding one row
to SCHEMA.md and one entry to README.md's unit list — not reformatting
unrelated JSON examples or the Commands table. Both files are within the
Touch list, so this isn't a Touch violation, but it is a formatting sweep
outside what any Step or acceptance criterion required, consistent with
CLAUDE.md's "Check the diff for scope creep" guidance (formatting sweeps
count as scope creep even when a repo convention/gate motivates them).
Recommend flagging to the task owner rather than silently accepting; it
does not affect the PASS verdict on the three acceptance criteria since
all specified checks pass and the semantic content is correct.
