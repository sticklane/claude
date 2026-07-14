# Task 02: Mirror the header-parsing consolidation to antigravity and bump plugin.json

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Priority values run P0 (highest) through P3; the header is optional — absent means P2. -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers, in every task file — and ## Progress / ## Deferred questions are drain-written sections (single writer, main checkout): workers report that content, never write it. -->

Status: done
Depends on: 01
Priority: P2
Budget: 12 turns
Spec: ../SPEC.md (Approach step 3; acceptance criterion 5)
Touch: antigravity/.agents/skills/_shared/headers.py, antigravity/.agents/skills/workboard/workboard.py, antigravity/.agents/skills/list-specs/list_specs.py, antigravity/.agents/skills/prioritize/prioritize_scan.py, antigravity/.agents/skills/workboard/test_workboard.py, antigravity/.agents/skills/prioritize/test_prioritize_scan.py, .claude-plugin/plugin.json

## Goal

Every `.py` file task 01 touched (including the new `headers.py`) has a
byte-identical counterpart under `antigravity/.agents/skills/`, with
exactly one named, permitted exception, and `.claude-plugin/plugin.json`'s
version is bumped in the same change, per CLAUDE.md's mirror convention.

## Touch

Do not touch any `.claude/skills/` file in this task — task 01 already
finalized that content; this task only mirrors it. Do not touch
`tests/test_antigravity_parity.sh` or `tests/test_antigravity_content_parity.sh`.

## Steps

1. Read every file task 01 touched under `.claude/skills/` (`_shared/headers.py`,
   `workboard/workboard.py`, `list-specs/list_specs.py`,
   `prioritize/prioritize_scan.py`, `workboard/test_workboard.py`,
   `prioritize/test_prioritize_scan.py`) in its final, task-01-merged form —
   do not assume task 01's task-file description is the literal diff; read
   the actual current file contents.
2. Copy each file's content to its `antigravity/.agents/skills/` counterpart
   path, with exactly one named exception: `prioritize_scan.py`'s module
   docstring may keep its existing standalone-install note (the sanctioned
   port divergence already live at `prioritize_scan.py`'s docstring vs its
   antigravity mirror) — this is the SOLE permitted divergence. Every other
   line, including all regex definitions, the `_load_module` import, and
   any other docstring content, must end up identical. The new
   `antigravity/.agents/skills/_shared/headers.py` should be fully
   byte-identical to its `.claude/skills/` counterpart (no docstring
   exception applies to it — it's a new file with no prior sanctioned
   divergence).
3. Bump `.claude-plugin/plugin.json`'s version (find the current value and
   its own bump convention — do not hard-code an assumed prior version;
   compare against the value at this task's own base commit, since a
   sibling task landing first in this run may have already bumped it).
4. Verify: for every touched `.py` file except `prioritize_scan.py`, run
   `diff <claude-path> <antigravity-path>` and confirm exit 0. For
   `prioritize_scan.py`, confirm the diff is empty except for the
   standalone-install docstring lines.
5. Run `bash tests/test_antigravity_parity.sh` and, if it exists on this
   tree, `bash tests/test_antigravity_content_parity.sh` — confirm both
   exit 0 (the mirror must not break either gate).
6. Commit.

## Acceptance

- [x] `diff -r` of every touched `.py` against its `antigravity/.agents/skills/` counterpart is empty, with the one named exception: `prioritize_scan.py`'s module docstring may keep its existing standalone-install note — every other line (all regex definitions, the `_load_module` import, any other docstring content) must diff empty
  - Evidence: `diff` of headers.py, workboard.py, list_specs.py, test_workboard.py, test_prioritize_scan.py all exit 0; `diff prioritize_scan.py` shows ONLY docstring lines 18-20 (the standalone-install note), everything else empty.
- [x] `.claude-plugin/plugin.json` version differs from its value at this task's own base commit (`git show <base-commit>:.claude-plugin/plugin.json | grep version` vs the current value)
  - Evidence: base commit 0284e23 had `"version": "0.9.5"`; bumped to `"version": "0.9.6"`.
- [x] `bash tests/test_antigravity_parity.sh` exits 0
  - Evidence: ran `bash tests/test_antigravity_parity.sh` → exit 0, no output.
- [x] `bash tests/test_antigravity_content_parity.sh` exits 0 (if present on this tree)
  - Evidence: ran `bash tests/test_antigravity_content_parity.sh` → exit 0, no output (the gate this task closes). Full `tests/test_*.sh` loop also all green.
