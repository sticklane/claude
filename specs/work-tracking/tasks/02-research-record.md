# Task 02: Work-tracking research record

Status: pending
Depends on: 01, ../../workflow-author/tasks/02-record-and-port-row.md
Priority: P3
Budget: 10 turns
Spec: ../SPEC.md (requirement R6)

## Goal

Append the "Work tracking" entry to docs/external-playbooks.md:
adoptions (follow-up-plus-dedupe, append-only/passes-only discipline
with the JSON-hard-to-mangle validation of our headers,
ExecPlans done-vs-remaining), the industry gap, and the declined items
with reasons. Spec R6 carries the exact content and URLs.

## Touch

- docs/external-playbooks.md (appender — dep on workflow-author 02 serializes)

## Acceptance

- [ ] `grep -qi "work tracking" docs/external-playbooks.md && sed -n '/[Ww]ork tracking/,/^## /p' docs/external-playbooks.md | grep -qi "append-only\|passes-only"` -> exit 0 (R6)
