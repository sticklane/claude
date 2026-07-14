# Task 01: Consolidate header regexes and _load_module into _shared/headers.py

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Priority values run P0 (highest) through P3; the header is optional — absent means P2. -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers, in every task file — and ## Progress / ## Deferred questions are drain-written sections (single writer, main checkout): workers report that content, never write it. -->

Status: pending
Depends on: none
Priority: P1
Budget: 22 turns
Spec: ../SPEC.md (Approach steps 1-2; acceptance criteria 1-4)
Touch: .claude/skills/_shared/headers.py, .claude/skills/workboard/workboard.py, .claude/skills/list-specs/list_specs.py, .claude/skills/prioritize/prioritize_scan.py, .claude/skills/workboard/test_workboard.py, .claude/skills/prioritize/test_prioritize_scan.py

## Goal

A single `.claude/skills/_shared/headers.py` module owns every `Key: value`
task-header regex (`STATUS_RE`, `DEPENDS_RE`, `PRIORITY_RE`, and any other
header regex `workboard.py` currently defines that its own consumers need)
plus the one `_load_module` bootstrap helper. `workboard.py`,
`list_specs.py`, and `prioritize_scan.py` all read these from `headers.py`
instead of defining or duplicating them locally, and the shared
`PRIORITY_RE` correctly reads `Priority: [P1]` as P1 and rejects out-of-range
values like `P7` (falls through to the `P2 (default)` behavior) in both
`workboard.py`'s and `prioritize_scan.py`'s scanning code paths.

## Touch

Do not touch `antigravity/.agents/skills/` in this task — that's task 02,
after this task's content is final. Do not touch `.claude-plugin/plugin.json`
here either (task 02). Do not change what any header value _means_ (P0-P3
semantics, defaults) beyond fixing the regex range — this is
parse-consistency only, per SPEC.md's Out of scope section.

## Steps

1. Read the current regex definitions and their exact current line numbers
   in `.claude/skills/workboard/workboard.py` (`STATUS_RE`, `DEPENDS_RE`,
   `PRIORITY_RE`) and the current `_load_module` definitions in
   `.claude/skills/list-specs/list_specs.py` and
   `.claude/skills/prioritize/prioritize_scan.py` — find their actual
   current form, do not assume the line numbers cited in SPEC.md's Problem
   section are still exact.
2. Create `.claude/skills/_shared/headers.py`: move `STATUS_RE`,
   `DEPENDS_RE`, and a `PRIORITY_RE` pinned to `\[?(P[0-3])\]?` (bracket-
   tolerant like workboard's current regex, but range-restricted to P0-P3 —
   fixing workboard's current `\[?(P\d)\]?` which incorrectly accepts any
   digit) into this new module, plus one `_load_module` helper (the
   byte-identical implementation currently duplicated in `list_specs.py`
   and `prioritize_scan.py`).
3. Pin the import mechanism to the viz-style pattern workboard.py already
   uses to reach `viz`/`spec_readiness`: `sys.path.insert(0, <path to
_shared>)` then `import headers` — a regular import, never
   path-loading (`_load_module`-by-path) for `headers.py` itself, since
   that would need a loader to load the loader.
4. Update `workboard.py` to import `STATUS_RE`, `DEPENDS_RE`, `PRIORITY_RE`
   from `headers` (via the sys.path.insert + import pattern) instead of
   defining them locally; remove the local definitions.
5. Update `list_specs.py` and `prioritize_scan.py` to import `_load_module`
   from `headers` (regular import, per step 3) instead of each defining
   its own copy; remove both local `_load_module` definitions. Both files
   still need to reach `workboard.py` itself (not moved into `_shared`) —
   they do this by calling the now-imported `_load_module` on
   `workboard.py`'s path, same as today.
6. Update `prioritize_scan.py` to use the shared `PRIORITY_RE` from
   `headers.py` in place of its own local `_PRIORITY_RE = re.compile(r"^Priority:\s*(P[0-3])", re.MULTILINE)`
   (no-brackets version) — remove the local definition.
7. Write the failing tests first, then make them pass: add a regression
   test to `.claude/skills/prioritize/test_prioritize_scan.py` and a
   symmetric one to `.claude/skills/workboard/test_workboard.py`, each
   asserting a fixture task file containing `Priority: [P1]` parses as P1
   (not the P2 default) via that file's own scanning code path. Add a
   second fixture/test pair in both files asserting `Priority: P7` does
   NOT match (falls through to the P2-default behavior) — this pins the
   P0-P3 range against future widening.
8. Run `python3 -m pytest .claude/skills` (scoped — do NOT widen to
   `antigravity/`, the mirror basenames collide on module names) and
   confirm it exits 0.
9. Commit.

## Acceptance

- [ ] `grep -rn "Priority:" .claude/skills/*/[a-z_]*.py | grep -c "re.compile"` returns 1 — a single compiled Priority regex definition, in `_shared/`, imported everywhere else
- [ ] A fixture task file containing `Priority: [P1]` yields P1 (not the P2 default) from both `prioritize_scan.py` and `workboard.py` scanning code paths, asserted by named tests in both test files
- [ ] A fixture task file containing `Priority: P7` does NOT match (falls through to P2 default) in both `prioritize_scan.py` and `workboard.py`, asserted by named tests in both test files
- [ ] `grep -c "def _load_module" .claude/skills/list-specs/list_specs.py .claude/skills/prioritize/prioritize_scan.py` shows 0 for both (loader lives in `_shared/` only)
- [ ] `python3 -m pytest .claude/skills` exits 0 (do not widen the run to `antigravity/` — mirror basenames collide)
