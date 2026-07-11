# Task 05: (tools) and (synthetic) buckets in by_model

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers. -->

Status: in-progress
Depends on: none
Priority: P2
Budget: 5 turns
Spec: ../SPEC.md (requirement R4)
Touch: agentprof/internal/costsummary/, agentprof/testdata/, specs/agentprof-attribution-gaps/evidence/

<!-- PLAN (delete at close-out)
1. RED: add costsummary_test.go tests — main-loop tool-duration sample
   ([...,"main","tool:Bash"], duration_ms) → by_model has "(tools)", no
   "main" key; subagent tool sample ([...,"agent:scout","tool:Read"]) →
   "(tools)", no agent: key; <synthetic> leaf keeps its own labeled row.
2. GREEN: modelLeaf returns "(tools)" sentinel when the leaf-most non-marker
   frame is structural (`main` or `agent:` — the model's parents), else the
   model. hasModel now always true for non-empty stacks.
3. <synthetic> choice = explicitly labeled (keeps its own bracketed row,
   calls preserved); document in code comment + ByModel doc note.
4. evidence/05-panel-check.md: agent-console _cost_rows iterates
   (dim or {}).items() generically — GENERIC-ITERATION, no fix needed.
-->


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

- [ ] `cd agentprof && go test ./internal/costsummary/` → pass including
  the no-`main`-key fixture
- [ ] evidence/05-panel-check.md records the agent-console check result
- [ ] `bash agentprof/scripts/check.sh` → green
