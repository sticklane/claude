# Task 02: Dependency-graph edges via resolve_dep (R3)

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Priority values run P0 (highest) through P3; the header is optional — absent means P2. -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers, in every task file — and ## Progress / ## Deferred questions are drain-written sections (single writer, main checkout): workers report that content, never write it. -->

Status: pending
Depends on: 01
Priority: P2
Budget: 10 turns
Spec: ../SPEC.md (requirement R3; Solution B; R5 invariant)
Touch: /Users/sjaconette/claude/.claude/skills/workboard/workboard.py, /Users/sjaconette/claude/.claude/skills/workboard/test_workboard.py

## Goal

`_spec_dag_tasks` resolves `Depends on:` entries through the existing `resolve_dep`/`_glob_task` instead of its bare `isdigit()` filter, so path-form, glob-form, and `specs/…`-rooted same-spec refs draw edges in the existing `viz.dag()` SVG. Cross-spec resolutions are excluded from the drawn graph; a spec with zero in-spec edges renders exactly as today (no `spec-dag` block); a cyclic `Depends on:` set returns without hanging.

## Touch

Only the two workboard skill files, and within workboard.py only the DAG data plumbing (`_spec_dag_tasks` and any helper it needs). Do NOT touch `live_session_ids`/`scan_sessions`/`assemble` (task 01), marker rendering/TEMPLATE (task 03), `.claude/skills/_shared/viz.py` (out of scope per SPEC.md), or `antigravity/` (task 04). Note: task 01 already landed on main — build on its merged state. Depends-on 01 exists ONLY because both tasks edit the same two files (merge serialization); there is no functional coupling.

## Steps

1. Write the failing tests first: (a) a spec fixture whose `Depends on:` entries use a non-bare-numeric same-spec form (e.g. a task-dir-relative path) yields HTML containing `<svg` with the expected edge drawn — confirm it fails under the current `isdigit()` filter (zero edges); (b) a fixture with a dependency cycle returns (no hang); (c) a spec with no deps yields no `spec-dag` block; (d) a cross-spec ref draws no edge.
2. Replace `_spec_dag_tasks`'s `isdigit()` filter with resolution through `resolve_dep`/`_glob_task`. Task dicts carry `abs`; derive `task_dir = Path(abs).parent` and `repo_root = Path(abs).parents[3]` (abs is `<repo>/specs/<slug>/tasks/NN-*.md`, per SPEC.md Solution B). Map each resolved in-spec file to its task `num`; drop cross-spec resolutions.
3. Do NOT re-implement cycle or empty-edge guards — `viz.dag()` is cycle-guarded and returns `""` with no edges; the workboard-level cycle test only proves the call returns.
4. Re-run the full suite; `TestSpecDagRendering` must keep passing.

## Acceptance

- [ ] `python3 -m pytest /Users/sjaconette/claude/.claude/skills/workboard/test_workboard.py -q` → all pass, including the new R3 tests (resolve_dep-form edge drawn, cycle returns, no-deps → no `spec-dag` block, cross-spec excluded) with `TestSpecDagRendering` unregressed
- [ ] `grep -nE '\.write_text|\.write\(|\bopen\([^)]*[\x27"][wax]' /Users/sjaconette/claude/.claude/skills/workboard/workboard.py` → still only the three known write sites — R5: no new writes
- [ ] `python3 /Users/sjaconette/claude/.claude/skills/workboard/workboard.py --out /tmp/wb-task02.html` → exits 0 and the HTML contains ≥1 dependency-graph `<svg` (this repo's specs declare in-spec deps)
