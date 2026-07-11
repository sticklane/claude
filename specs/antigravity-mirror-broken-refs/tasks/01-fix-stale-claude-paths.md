# Task 01: Fix stale `.claude/skills/<name>` path references in the antigravity mirror

Status: done
Depends on: none
Priority: P1
Budget: 6 turns
Spec: ../SPEC.md (items #1, #4)
Touch: antigravity/.agents/skills/workboard/reference.md, antigravity/.agents/skills/workboard/test_workboard.py, antigravity/.agents/skills/list-specs/test_list_specs.py, antigravity/.agents/skills/prioritize/test_prioritize_scan.py

## Goal

All four files read `.agents/skills/<name>` in their run instructions
instead of the stale `.claude/skills/<name>` — a path that doesn't exist
in a standalone Antigravity install (only `.claude/`-source repos have
both trees; a consumer install only has `.agents/`).

## Touch

Four files only, each a single-line-class fix (a `Run:` docstring header
or an inline shell command). Do not touch any other file under
`antigravity/.agents/skills/prioritize/` — task 03 owns
`prioritize_scan.py` and a new `README.md` there; this task only touches
`test_prioritize_scan.py`'s header.

## Steps

1. In `antigravity/.agents/skills/workboard/reference.md:13`, change
   `python3 -m unittest discover -s .claude/skills/workboard` to
   `.agents/skills/workboard`.
2. In `antigravity/.agents/skills/workboard/test_workboard.py`'s docstring
   header (`Run:` line, near the top), change `.claude/skills/workboard`
   to `.agents/skills/workboard`.
3. In `antigravity/.agents/skills/list-specs/test_list_specs.py`'s
   docstring header (two `Run:`/`or:` lines), change both
   `.claude/skills/list-specs` occurrences to `.agents/skills/list-specs`.
4. In `antigravity/.agents/skills/prioritize/test_prioritize_scan.py`'s
   docstring header (two `Run:`/`or:` lines), change both
   `.claude/skills/prioritize` occurrences to `.agents/skills/prioritize`.
5. Run the affected test suites to confirm the edits are comment-only and
   don't break collection.

## Acceptance

- [x] `grep -rn '\.claude/skills/' antigravity/.agents/skills/workboard/reference.md antigravity/.agents/skills/workboard/test_workboard.py antigravity/.agents/skills/list-specs/test_list_specs.py antigravity/.agents/skills/prioritize/test_prioritize_scan.py` → no output
- [x] `cd antigravity/.agents/skills/workboard && python3 -m pytest -q` → 93 passed
- [x] `cd antigravity/.agents/skills/list-specs && python3 -m pytest -q` → 30 passed
- [x] `cd antigravity/.agents/skills/prioritize && python3 -m pytest -q` → 17 passed
