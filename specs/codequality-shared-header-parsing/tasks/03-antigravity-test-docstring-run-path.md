# Task 03: Reconcile antigravity Run-path docstring adaptation

Status: done
Promotion-ready: true
Promoted-by-run: c92aedb1ae49f8d3
Depends on: none
Priority: P2
Budget: 3 turns
Spec: ../SPEC.md
Touch: antigravity/.agents/skills/workboard/test_workboard.py, antigravity/.agents/skills/prioritize/test_prioritize_scan.py

## Goal

Re-apply the sanctioned `.agents/skills/` Run-path docstring adaptation to
`antigravity/.agents/skills/workboard/test_workboard.py` and
`antigravity/.agents/skills/prioritize/test_prioritize_scan.py`, matching the
pattern already preserved in `antigravity/.agents/skills/list-specs/test_list_specs.py`
and confirmed sanctioned by the sibling `codequality-antigravity-content-parity`
spec's task 01. Task 02 of this spec made these two files fully byte-identical
to their `.claude/skills/` counterparts to satisfy its literal acceptance
criterion, which incidentally dropped this docstring adaptation -- this task
restores it, resolving the inconsistency with the sibling spec's outcome.

## Touch

Only the two antigravity test files' `Run:` docstring lines. This is an
antigravity-side-only fix (no `.claude/skills/` file changes), so no further
mirror or `plugin.json` bump obligation applies.

## Steps

1. Update `antigravity/.agents/skills/workboard/test_workboard.py`'s `Run:`
   docstring line to reference `.agents/skills/workboard` instead of
   `.claude/skills/workboard`.
2. Update `antigravity/.agents/skills/prioritize/test_prioritize_scan.py`'s
   two `Run:`-adjacent docstring lines to reference `.agents/skills/prioritize`
   instead of `.claude/skills/prioritize`.
3. Confirm both antigravity parity gates stay green (they already exclude
   these files/paths from byte-diff checks per prior sanctioned-adaptation
   precedent).

## Acceptance

- [x] `grep -q '.agents/skills/workboard' antigravity/.agents/skills/workboard/test_workboard.py`
- [x] `grep -c '.agents/skills/prioritize' antigravity/.agents/skills/prioritize/test_prioritize_scan.py` → 2
- [x] `diff -q .claude/skills/workboard/test_workboard.py antigravity/.agents/skills/workboard/test_workboard.py; [ $? -ne 0 ]` (differs only on the Run: line)
- [x] `diff -q .claude/skills/prioritize/test_prioritize_scan.py antigravity/.agents/skills/prioritize/test_prioritize_scan.py; [ $? -ne 0 ]` (differs only on the Run: lines)
- [x] `bash tests/test_antigravity_content_parity.sh` → exit 0
- [x] `bash tests/test_antigravity_parity.sh` → exit 0
