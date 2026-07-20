# Task 01: drain_frontier.py scanner, unit tests, and golden fixture

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch, Rigor) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. -->

Status: done
Depends on: none
Priority: P1
Budget: 16 turns
Spec: ../SPEC.md (requirements R1, R2)
Touch: .claude/skills/drain/drain_frontier.py, .claude/skills/drain/test_drain_frontier.py, .claude/skills/drain/fixtures/

## Goal

The scanner exists exactly per R1's pinned field semantics (dispatchable
⊇ admissible; no live-slot arithmetic; empty-window assumption; Group
predicate + separate claim-set disjointness; conservative glob prefix
predicate; per-spec invocation; the two-tier parse semantics), loading
`_shared/headers.py` via the same importlib bootstrap as
`list_specs.py`. `test_drain_frontier.py` covers every R2 case, and the
one committed golden fixture lives at
`.claude/skills/drain/fixtures/basic-window/` — never under `specs/`.

## Steps

1. Read SPEC.md R1/R2 in full, `.claude/skills/drain/reference.md`'s
   Rolling-window admission section (the authority), and
   `list_specs.py`'s bootstrap.
2. Write the failing tests first — every R2 case, including
   `min(N, candidates)` with non-empty `--claimed` and the
   malformed-Status non-zero exit.
3. Implement until green; keep it stdlib-only, read-only, deterministic.
4. Build the committed golden fixture with a documented expected
   `admissible` for `--window 2`.

## Acceptance

- [x] `python3 .claude/skills/drain/test_drain_frontier.py` → exit 0,
      with at least one test per R2 incident class
      Evidence: 22 tests pass, exit 0; one TestCase per R2 incident class (evidence/01-scanner-and-tests.md).
- [x] `python3 .claude/skills/drain/drain_frontier.py
  .claude/skills/drain/fixtures/basic-window --window 2` → JSON
      whose `admissible` matches the fixture's documented expectation
      Evidence: exit 0, admissible = [02-alpha.md, 03-beta.md], matches fixtures/basic-window/EXPECTED.md (evidence/01-scanner-and-tests.md).
- [x] `[ ! -d specs/basic-window ] && ! ls .claude/skills/drain/fixtures/
  | grep -qv basic-window` → exit 0 (fixture landed in the skill
      dir only; nothing stray)
      Evidence: command exits 0; fixtures/ contains only basic-window/ (evidence/01-scanner-and-tests.md).

## Decisions

- JSON `blocked` entries use reason tags `unmet-deps` / `unresolved-external-dep` / `unblock`; reversible — rename in drain_frontier.py if drain (task 02) prefers other keys.
- Malformed Status/Depends exits code 2 (any non-zero satisfies the spec); reversible — change the `return 2` in main().
- Golden fixture documents its expectation in fixtures/basic-window/EXPECTED.md (kept inside basic-window/ so `ls fixtures/` stays clean); reversible — move the doc.
- Rejected review finding: a scout suggested making all Touch-disjoint tasks co-admissible when a spec defines no `- Group:` lines. Not applied — it contradicts R1's pinned "a task on no `- Group:` line runs alone, admitted only when the window is empty", which the ungrouped-runs-alone tests assert.
