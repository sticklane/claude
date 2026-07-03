# Task 02: Ultracode research record and antigravity port row

Status: done
Depends on: 01, ../../model-agnostic/tasks/04-antigravity-mirrors.md, ../../task-priority/tasks/02-research-record.md
Priority: P3
Budget: 10 turns
Spec: ../SPEC.md (requirements R5, R7)

## Goal

Append the "Workflow scripts (ultracode)" entry to
docs/external-playbooks.md (plugins cannot ship workflows — or the
corrected wording if task 01's R6 evidence says otherwise; opt-in gate
cites docs/human-gates.md; runtimes/ Orchestration cross-ref) and add
the launch-list degradation row to antigravity/README.md's mapping
table. Spec R5/R7 are exact.

## Touch

- docs/external-playbooks.md (appender — dep on task-priority 02 serializes)
- antigravity/README.md (also edited by model-agnostic 04 — dep serializes)

## Acceptance

- [x] `grep -qi "workflow scripts (ultracode)" docs/external-playbooks.md && sed -n '/[Ww]orkflow scripts (ultracode)/,/^## /p' docs/external-playbooks.md | grep -Eqi "cannot ship workflows|can now ship workflows"` -> exit 0 (R5) — verifier confirmed exit 0 and all three R5 content elements (see ../evidence/02-record-and-port-row.md)
- [x] `grep -qi "launch-list" antigravity/README.md` -> exit 0 (R7) — verifier confirmed exit 0; one mapping-table row, launch-list degradation (see ../evidence/02-record-and-port-row.md)
