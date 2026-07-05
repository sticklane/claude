# Task 01: `open_questions_unresolved` shared helper

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Priority values run P0 (highest) through P3; the header is optional — absent means P2. -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers, in every task file — and ## Progress / ## Deferred questions are drain-written sections (single writer, main checkout): workers report that content, never write it. -->

Status: in-progress
Depends on: none
Priority: P0
Budget: 8 turns
Spec: ../SPEC.md (R0, R0-note)
Touch: .claude/skills/_shared/spec_readiness.py, .claude/skills/_shared/test_spec_readiness.py

## Goal

`.claude/skills/_shared/spec_readiness.py` exports
`open_questions_unresolved(spec_md_text: str) -> bool`, matching R0's exact
contract, with a green test suite covering all seven listed cases. This
module is the foundation both Task 02 (this spec) and, later, `/prioritize`
depend on — nothing downstream can be built until this contract is right.

## Touch

Only the two new files above. Do not touch `.claude/skills/workboard/*` or
`.claude/skills/_shared/viz.py` — this task adds a sibling module, it
doesn't modify the existing shared helpers.

**Coordination hazard (R0-note):** `specs/workboard-auto-triage`'s own R0
may also create this exact file. As of this writing that spec has no
`tasks/` dir (not yet broken down), so there is no live collision — but
check anyway: if `.claude/skills/_shared/spec_readiness.py` already exists
when you start (created by a concurrent run you weren't aware of), do not
blindly overwrite it. Read it, run the required test cases against it, and
only replace it if it fails to satisfy R0's contract.

## Steps

1. Check whether `.claude/skills/_shared/spec_readiness.py` already exists.
   If yes, skip to step 4 (verify, don't blindly rewrite).
2. Write the failing tests first, in
   `.claude/skills/_shared/test_spec_readiness.py`, one per R0 case:
   - `## Open questions` heading absent → `False`
   - heading present, body blank → `False`
   - body exactly `(none)` → `False`
   - body single-line `(none — ready for breakdown)` → `False`
   - body the multi-line example from R0 (3 lines, `(none — ...)` opening
     the parenthetical) → `False`
   - body containing real unresolved prose → `True`
   - heading is the last thing in the file (EOF, no trailing `## `) → its
     own case per the value of the trailing body (blank → `False`,
     unresolved prose → `True`)
   Run them and confirm they fail (the module doesn't exist yet).
3. Implement `open_questions_unresolved` in
   `.claude/skills/_shared/spec_readiness.py`: locate the `## Open
   questions` heading (case-sensitive, matching this repo's convention);
   extract the body up to the next `## ` heading or EOF; collapse all
   internal whitespace (including newlines) to single spaces and strip
   both ends; return `False` if the result is empty, or matches
   (case-insensitively) `none`, `(none)`, or `(none` followed by an
   em-dash or hyphen and any trailing text ending in `)`; return `True`
   for everything else, and `False` when the heading is absent entirely.
4. Run `pytest .claude/skills/_shared/test_spec_readiness.py -v` until
   green.

## Acceptance

- [ ] `pytest .claude/skills/_shared/test_spec_readiness.py -v` → all
      seven R0 cases pass.
- [ ] `python3 -c "import sys; sys.path.insert(0, '.claude/skills/_shared'); import spec_readiness; print(spec_readiness.open_questions_unresolved('## Open questions\n\n(none)\n'))"` → prints `False`.
- [ ] `python3 -c "import sys; sys.path.insert(0, '.claude/skills/_shared'); import spec_readiness; print(spec_readiness.open_questions_unresolved('## Open questions\n\nStill deciding X.\n'))"` → prints `True`.
