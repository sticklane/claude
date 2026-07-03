# Task 02: Task-prioritization research record

Status: in-progress
Depends on: 01, ../../tournament-votes/tasks/01-majority-votes.md
Priority: P3
Budget: 10 turns
Spec: ../SPEC.md (requirement R4)

## Goal

Append the "Task prioritization" entry to docs/external-playbooks.md:
the ready-set/waves convergence with the six pinned URLs, the
no-vendor-ranking gap, and the two adopted signals (Anthropic
highest-priority-one-at-a-time; OpenAI PoC-first). Spec R4 carries the
exact content and URLs.

## Touch

- docs/external-playbooks.md (appender — dep on tournament-votes 01 serializes the chain)

## Acceptance

- [ ] `grep -qi "task prioritization" docs/external-playbooks.md && sed -n '/[Tt]ask prioritization/,/^## /p' docs/external-playbooks.md | grep -qi "ready set"` -> exit 0 (R4)
