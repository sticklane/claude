# Task 01: drain_frontier.py scanner, unit tests, and golden fixture

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch, Rigor) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. -->

Status: pending
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

- [ ] `python3 .claude/skills/drain/test_drain_frontier.py` → exit 0,
      with at least one test per R2 incident class
- [ ] `python3 .claude/skills/drain/drain_frontier.py
    .claude/skills/drain/fixtures/basic-window --window 2` → JSON
      whose `admissible` matches the fixture's documented expectation
- [ ] `[ ! -d specs/basic-window ] && ! ls .claude/skills/drain/fixtures/
    | grep -qv basic-window` → exit 0 (fixture landed in the skill
      dir only; nothing stray)
