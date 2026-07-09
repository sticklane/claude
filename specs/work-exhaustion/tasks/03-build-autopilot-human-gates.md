# Task 03: Build/autopilot decision rule + human-gates revision

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Priority values run P0 (highest) through P3; the header is optional — absent means P2. -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers, in every task file — and ## Progress / ## Deferred questions are drain-written sections (single writer, main checkout): workers report that content, never write it. -->

Status: in-progress
Depends on: none
Priority: P2
Budget: 12 turns
Spec: ../SPEC.md (requirements R3 build-side, R4 autopilot-side, R5 build-side, R6)
Touch: .claude/skills/build/SKILL.md, .claude/skills/autopilot/SKILL.md, docs/human-gates.md

## Goal

`build/SKILL.md` applies the reversible-default rule attended (take the
default, log to the task file's `## Decisions` at close-out; gate-list
decisions still stop and surface) and names /handoff as the
heavy-context escape for attended runs. `autopilot/SKILL.md` gains the
three-section exit checklist (defaults taken — read from `## Decisions`,
which autopilot's /build-procedure dispatch already produces with no
separate edit — the task's blocker if any, and the next command).
`docs/human-gates.md`'s final self-chain section is REVISED so the
auto-/breakdown authorization is the critic's independent READY verdict
whether written earlier or in-session during drain's critique intake, and
states that gates govern launch, not continuation; the "before drain ever
looks" sentence is rewritten.

## Touch

Only the three files in the header. Do NOT touch `drain/SKILL.md` (task 01) or `drain/reference.md` (task 02), nor `antigravity/` /
`.claude-plugin/plugin.json` (task 04).

## Steps

1. Read `../SPEC.md` Solution 3–5 and R3–R6 (the clauses naming /build,
   autopilot, and human-gates).
2. build/SKILL.md: add the reversible-default rule (mirroring the spec's
   Solution 3 wording; the `## Decisions` name is pinned) and the
   attended /handoff escape.
3. autopilot/SKILL.md: add the three-section checklist to its
   walk-away/close-out contract.
4. docs/human-gates.md: rewrite the final self-chain section per R6 —
   revise, don't append; include the word "continuation"; remove the
   literal "before drain ever looks".
5. Run the acceptance greps and `bash evals/lint-ultra-gate.sh` (build is
   an ultra-path skill).

## Acceptance

- [ ] `grep -qi "reversible default" .claude/skills/build/SKILL.md` → match
- [ ] `grep -q "## Decisions" .claude/skills/build/SKILL.md` → match
- [ ] `grep -qi "checklist" .claude/skills/autopilot/SKILL.md` → match
- [ ] `grep -qi "continuation" docs/human-gates.md` → match
- [ ] `grep -c "before drain ever looks" docs/human-gates.md` → 0
- [ ] `bash evals/lint-ultra-gate.sh` → exit 0
