# Task 03: workboard.py HUMAN.md scanner + inbox category

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers. -->

Status: done
Depends on: 01
Priority: P1
Budget: 6 turns
Spec: ../SPEC.md (requirement R4)
Touch: .claude/skills/workboard/workboard.py, .claude/skills/workboard/test_workboard.py, antigravity/.agents/skills/workboard/workboard.py, antigravity/.agents/skills/workboard/test_workboard.py

## Goal

`workboard.py` (the single scan/inbox source; agent-console.py is
adapter-only and unchanged) gains a HUMAN.md scanner: parse `- [ ]`
entries under `## Agent-filed blockers` per repo into attention_items
(date, repo, type, ask) surfaced above spec/task rows; `- [x]` skipped;
absent file/section graceful. Tests first in test_workboard.py (fixture
pair per SPEC). Port BOTH .py files to antigravity byte-identically
(`cp` + `diff -q`, docs/memory/workboard-mirror-verbatim.md) in the same
commit.

## Acceptance

- [x] `python3 -m pytest .claude/skills/workboard/test_workboard.py -q` → pass incl. the fixture pair (two open + one checked → two rows; no HUMAN.md → no rows, no error) — verifier: `128 passed`; fixture pair confirmed genuine (evidence/03-workboard-scanner.md)
- [x] `diff -q .claude/skills/workboard/workboard.py antigravity/.agents/skills/workboard/workboard.py && diff -q .claude/skills/workboard/test_workboard.py antigravity/.agents/skills/workboard/test_workboard.py` → identical — verifier: both pairs byte-identical, exit 0 (evidence/03-workboard-scanner.md)
- [x] `bash agent-console/scripts/check.sh` → green (adapter untouched or pass-through only) — verifier: `check: PASS` (147 tests); diff --stat shows only the 4 workboard files, agent-console.py untouched (evidence/03-workboard-scanner.md)
