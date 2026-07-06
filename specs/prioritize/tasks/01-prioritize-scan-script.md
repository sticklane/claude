# Task 01: prioritize_scan.py — scan + table script (TDD)

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Priority values run P0 (highest) through P3; the header is optional — absent means P2. -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers, in every task file — and ## Progress / ## Deferred questions are drain-written sections (single writer, main checkout): workers report that content, never write it. -->

Status: pending
Depends on: none
Priority: P1
Budget: 20 turns
Spec: ../SPEC.md (requirements R1, R2)
Touch: .claude/skills/prioritize/prioritize_scan.py, .claude/skills/prioritize/test_prioritize_scan.py

## Goal

`.claude/skills/prioritize/prioritize_scan.py` exists and, run with
`python3` from any repo, prints a markdown table `Ref | Title | Status |
Priority` of every task across every non-archive spec whose status is
`pending`, `blocked`, or `deferred` — or the exact line "nothing to
reprioritize" when none qualify. It reuses `scan_toolkit_specs` from
`.claude/skills/workboard/workboard.py` via the established
`importlib.util.spec_from_file_location` absolute-path pattern and adds its
own `Priority:` header regex parse over each task's `abs` file (the scanner
dict has no priority key — keys are `file`, `abs`, `title`, `status`,
`deps`).

## Touch

Only the two new files under `.claude/skills/prioritize/`. Do NOT modify
`.claude/skills/workboard/workboard.py` (reuse it read-only via importlib)
or anything under `.claude/skills/list-specs/`. No SKILL.md in this task —
task 02 owns the skill prose and the antigravity mirror.

## Steps

1. Write failing tests first in
   `.claude/skills/prioritize/test_prioritize_scan.py` (model:
   `.claude/skills/list-specs/test_list_specs.py`, including its
   derive-repo-root-from-`.git`-marker approach — never a fixed parent
   depth). Fixture repos in `tmp_path` covering:
   - zero pending/blocked/deferred tasks → output is "nothing to
     reprioritize", no table;
   - 2 specs with a mix of pending/blocked/deferred/done/draft/failed/
     in-progress tasks → only pending/blocked/deferred rows appear;
     `done`, `skipped`, `in-progress`/`in_progress`/`claimed`, `draft`,
     `failed` never do;
   - `Ref` rendered as `<spec-slug>/<task-filename>`; rows sorted by spec
     slug then task number;
   - a task with a `Priority:` header shows that value; a task without
     one shows `P2 (default)`;
   - a header-less task file (no `Status:` line) is listed as `pending`
     (scanner default);
   - a spec under `specs/archive/` is excluded.
   Assert structure (parse rows), not exact whole-output strings.
2. Run the tests; confirm they fail for the right reason.
3. Implement `prioritize_scan.py`: locate `workboard.py` relative to the
   script's own path (`.claude/skills/workboard/workboard.py`), load via
   `importlib.util.spec_from_file_location`, call `scan_toolkit_specs`
   against the cwd repo, filter statuses per R1, regex-parse
   `^Priority:\s*(P[0-3])` (single-line header above the first `##`
   heading) from each task's `abs` content, and print the R2 table sorted
   by spec slug then task number.
4. Green, then refactor with tests passing.

## Acceptance

- [ ] `python3 -m pytest .claude/skills/prioritize/test_prioritize_scan.py -q` → all pass
- [ ] `cd /Users/sjaconette/claude && python3 .claude/skills/prioritize/prioritize_scan.py` → prints a table containing `Ref | Title | Status | Priority` header with only pending/blocked/deferred rows and no `archive/` refs (or "nothing to reprioritize" if the repo has none at run time)
- [ ] `bash scripts/check.sh` → green
