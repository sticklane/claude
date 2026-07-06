# Task 02: `list_specs.py` scan + bucket + classify script

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Priority values run P0 (highest) through P3; the header is optional — absent means P2. -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers, in every task file — and ## Progress / ## Deferred questions are drain-written sections (single writer, main checkout): workers report that content, never write it. -->

Status: done
Depends on: 01
Priority: P1
Budget: 14 turns
Spec: ../SPEC.md (Solution, R1-R6)
Touch: .claude/skills/list-specs/list_specs.py, .claude/skills/list-specs/test_list_specs.py

## Goal

`.claude/skills/list-specs/list_specs.py` scans `specs/` under the cwd,
buckets every task by status (R3), classifies each spec into exactly one
next-command row per R4's 10-rule precedence order, and prints one
markdown table (R5) — with a green fixture-based test suite covering every
branch.

## Touch

Only the two new files above, under `.claude/skills/list-specs/`. Do not
edit `.claude/skills/workboard/workboard.py` or
`.claude/skills/_shared/spec_readiness.py` — this task consumes both as
read-only dependencies, it doesn't modify them. Do not create
`.claude/skills/list-specs/SKILL.md` — that's Task 03.

## Steps

1. Write the failing tests first, in
   `.claude/skills/list-specs/test_list_specs.py`, using
   `tempfile.TemporaryDirectory()` fixtures in the same style as
   `.claude/skills/workboard/test_workboard.py` (build a real `specs/`
   tree under the tmp dir, call the script's functions, assert on
   structured output — no mocking). Cover every acceptance-criteria case
   listed below before writing the implementation.
2. Implement `list_specs.py`:
   - Load `scan_toolkit_specs` and `read_text` from
     `.claude/skills/workboard/workboard.py` via
     `importlib.util.spec_from_file_location` on that file's **absolute
     path** (computed relative to this script's own `__file__`) — not a
     bare `import workboard`. Note loading workboard.py this way executes
     its top-level `sys.path.insert(0, .../_shared)` + `import viz`, so
     `viz.py` must keep importing cleanly; workboard's own CLI logic stays
     inert behind its `if __name__ == "__main__"` guard.
   - Import `open_questions_unresolved` from
     `.claude/skills/_shared/spec_readiness.py` (sibling of `viz.py` on
     the `_shared` path workboard.py's import already added to
     `sys.path`, or via the same `spec_from_file_location` technique —
     pick whichever composes cleanly with the load above).
   - R1: no `specs/` directory under cwd → print the one-line message,
     `sys.exit(0)`.
   - R2: rely on `scan_toolkit_specs` already requiring `spec_dir/SPEC.md`
     to be a file (workboard.py:220) — no separate archive filtering
     needed; add a test that proves it holds.
   - R3: for each spec with `tasks_total > 0`, bucket every task's raw
     `status` string into exactly one of `pending_like` / `in_progress_like`
     / `deferred` / `blocked_or_failed` / `draft` / `done_like` /
     `unrecognized`, per the literal string lists in R3. A spec with
     `tasks_total == 0` (missing or empty `tasks/`) skips bucketing
     entirely — its status summary is `"no tasks/"`.
   - R4: classify each spec into exactly one of the 10 precedence rules,
     first match wins. Implement this as an explicit ordered `if/elif`
     chain mirroring the spec's numbering — do not "simplify" the
     ordering, since rules 3 vs 5, 4 vs 3, 8 vs 10 depend on it.
   - R5: render one markdown table, columns `Spec | Status | Next
     command`, rows sorted alphabetically by spec slug, to stdout only.
   - R6: no argparse / no CLI flags — always scans `Path.cwd() / "specs"`.
3. Run `pytest .claude/skills/list-specs/test_list_specs.py -v` until
   green.

## Acceptance

- [x] `pytest .claude/skills/list-specs/test_list_specs.py -v` passes,
      with a test for each of: no `specs/` dir (R1); archive-only repo →
      zero data rows (R2); no `tasks/` + unresolved Open questions →
      `/critique`; no `tasks/` + resolved/absent Open questions →
      `/breakdown`; `tasks/` present but empty → same as no `tasks/`;
      2 pending + 1 done → `/drain`; exactly 1 pending task →
      `/build specs/<slug>/tasks/<file>`; deferred + 2 pending →
      `/drain` (deferred precedence); blocked + 2 pending → flagged
      `blocked/failed`, no command (rule 4 over rule 5); deferred +
      blocked, no pending → `/drain` (rule 3 over rule 4); all
      claimed/in-progress → flagged `in-progress/awaiting`, no command;
      all done + one draft → flagged `drafts ready for promotion`; all
      done, no drafts → `/distill`; one task with missing `Status:`
      header → counts as `pending_like`; one task with unrecognized
      status, no others → flagged `unrecognized task status`; one draft +
      one unrecognized status → flagged `unrecognized` (rule 10 over rule
      8); no `tasks/` + Open questions body exactly `(none)` →
      `/breakdown`, not `/critique`.
      Evidence: 30 passed in 0.09s (ran in this task's worktree, same
      path relative to repo root:
      `.claude/skills/list-specs/test_list_specs.py`).
- [x] `cd /tmp && mkdir -p emptyrepo && cd emptyrepo && python3 /Users/sjaconette/claude/.claude/skills/list-specs/list_specs.py` → prints the no-specs message and exits 0.
      Evidence: run against this task's isolated worktree copy (the
      shared-checkout path this branch will land on doesn't have the file
      until merge) — `python3 <worktree>/.claude/skills/list-specs/list_specs.py`
      from `/tmp/emptyrepo` printed `no specs/ directory found`, exit 0.
- [x] `cd /Users/sjaconette/claude && python3 .claude/skills/list-specs/list_specs.py` → prints a markdown table of this repo's current active specs, no crash, no `archive/` rows.
      Evidence: run as `python3 .claude/skills/list-specs/list_specs.py`
      from this task's worktree root (same repo content as
      `/Users/sjaconette/claude`, isolated per drain's worktree
      convention) — printed a 9-row markdown table (absorb-agent-tools,
      drain-rolling-window, drain-sweep-preservation, list-specs,
      multi-session-coordination, precommit-review, shared-viz-renderer,
      skill-profiling-workboard, workboard-cli-graphs-health), exit 0, no
      `archive/` rows (verified `specs/archive/` has no top-level
      `SPEC.md`, so `scan_toolkit_specs` already excludes it per R2).
