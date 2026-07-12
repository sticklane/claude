# Task 05: SCHEMA.md overview of the full cost-summary output JSON

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers. -->

Status: draft
Discovered-from: specs/cache-reprime-visibility/tasks/04-docs.md
Depends on: none
Priority: P3
Budget: 3 turns
Spec: ../SPEC.md
Touch: agentprof/SCHEMA.md

## Goal

SCHEMA.md documents the cost-summary output JSON as a whole: one section
listing every top-level key (`by_project`, `by_skill`, `by_agent_type`,
`by_model`, `totals`, `sessions_added`, `reprime`, `sessions`) with a
one-line meaning each, placed beside the existing reprime/sessions
sections. Docs follow code: verify the key list against the `Summary`
struct in `agentprof/internal/costsummary/costsummary.go` before writing.

## Original report

> SCHEMA.md documents the canonical input sample schema but has no
> overview of the "Cost (7d)" summary output JSON as a whole — task 04
> added only the reprime/sessions sections it required; the other summary
> keys (by_project/by_skill/by_agent_type/by_model/totals/sessions_added)
> remain undocumented in SCHEMA.md (out of that task's scope).

## Acceptance

- [ ] `grep -c 'sessions_added' agentprof/SCHEMA.md` ≥ 1 AND
  `grep -c 'by_agent_type' agentprof/SCHEMA.md` ≥ 1 (both absent from
  SCHEMA.md today — that gap is what this stub records)
- [ ] MANUAL: every field of the `Summary` struct appears in the overview
  section, none invented
- [ ] `bash agentprof/scripts/check.sh` → green (docs only)
