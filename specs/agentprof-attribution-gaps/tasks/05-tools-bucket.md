# Task 05: (tools) and (synthetic) buckets in by_model

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers. -->

Status: done
Depends on: none
Priority: P2
Budget: 5 turns
Spec: ../SPEC.md (requirement R4)
Touch: agentprof/internal/costsummary/, agentprof/testdata/, specs/agentprof-attribution-gaps/evidence/

## Goal

`modelLeaf()` (costsummary.go:~100) returns a sentinel for samples with no
model frame; the summary shows them as `(tools)` — `main` never appears as
a by_model key. `<synthetic>` keeps its own row but is excluded from
`calls` aggregation OR explicitly labeled — pick one and document the
choice in a code comment + the summary's doc note. The agent-console
workboard cost panel is checked for special-casing of the literal `main`
key (expected: generic key iteration); the check is recorded in evidence/,
and the panel fixed only if it special-cases.

## Touch

costsummary only (agent-console is read-only inspection unless a
special-case is found — if a panel fix is needed, record it in evidence/
and make the minimal edit). Parallel-safe against tasks 01–04
(internal/claude/); do NOT touch that package.

## Steps

1. Failing test first: fixture with main-loop tool-duration samples →
   by_model has `(tools)`, no `main` key.
2. Implement the sentinel; decide and document the `<synthetic>` choice.
3. Inspect the agent-console panel for `main` special-casing; write
   evidence/05-panel-check.md.

## Acceptance

- [x] `cd agentprof && go test ./internal/costsummary/` → pass including
  the no-`main`-key fixture — `ok github.com/sticklane/agentprof/internal/costsummary`; TestBuildToolDurationSamplesBucketUnderToolsNotMain asserts no `main` key + `(tools)` holds duration_ms=1500
- [x] evidence/05-panel-check.md records the agent-console check result —
  GENERIC-ITERATION (`_cost_rows` iterates `(dim or {}).items()`); no panel fix needed
- [x] `bash agentprof/scripts/check.sh` → green — format-check ok / lint ok / tests ok

## Decisions

- `<synthetic>` by_model handling: chose **explicitly labeled** over
  excluded-from-calls. It keeps its own distinctly-named `<synthetic>` row
  (bracketed name marks it non-model) with `calls` preserved. Reversible:
  to switch to calls-exclusion, skip the `calls` sample_type for `<synthetic>`
  in Build's by_model add loop.
