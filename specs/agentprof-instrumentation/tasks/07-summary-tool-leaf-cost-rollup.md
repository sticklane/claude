# Task 07: Exclude tool/pending leaves from the summary cost rollup

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers. -->

Status: pending
Depends on: none
Priority: P3
Budget: 6 turns
Spec: ../SPEC.md
Discovered-from: 01-tool-and-model-durations.md
Touch: agentprof/summary.go, agentprof/summary_test.go

## Goal

`-o summary` mode (`agentprof/summary.go`) no longer emits zero-cost rows
keyed `model=tool:<name>` / `tool:(pending)`: the (session, model) cost
rollup derives its model from the last leaf frame that is NOT a
`tool:`/`role:`/`stage:` frame — the same rule
`specs/workboard-weekly-cost-view/SPEC.md` already pins for its own
grouping — instead of the raw stack leaf.

## Answers

Decision (recorded at promotion, 2026-07-09, per the maintainer's
standing decision-deferral policy): EXCLUDE tool/pending leaves from the
summary rollup. Rationale: workboard-weekly-cost-view SPEC's model
definition already excludes `tool:` frames, and nothing downstream
consumes `-o summary`'s tool rows. Reversible by reverting the single
grouping branch if a downstream consumer for tool rows appears.

## Steps

1. Write the failing test first: assert no summary row's model has
   prefix `tool:` against a fixture containing tool samples.
2. Change the model derivation in `summary.go` to skip
   `tool:`/`role:`/`stage:` leaf frames (mirror the costsummary rule).
3. Green + gates.

## Acceptance

- [ ] `cd agentprof && go test ./... -run Summary` → pass, including the new red-first test asserting no row has model prefix `tool:`
- [ ] `cd agentprof && bash scripts/check.sh` → exit 0
