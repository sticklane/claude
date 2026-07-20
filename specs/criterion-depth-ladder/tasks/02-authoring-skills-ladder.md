# Task 02: Teach /idea and /breakdown ladder classification at draft time

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch, Rigor) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. -->

Status: in-progress
Depends on: 01
Priority: P2
Budget: 8 turns
Spec: ../SPEC.md (requirements R2, R3)
Touch: .claude/skills/idea/SKILL.md, .claude/skills/breakdown/SKILL.md

## Goal

/idea's anchoring step additionally classifies each drafted criterion's
ladder level and applies the deepest-feasible rule (with `Depth ceiling:`
annotations for L0-capped requirements) at draft time; /breakdown applies
the same rule to task `## Acceptance` sections. Both cite
`docs/memory/anchored-acceptance-criteria.md` (task 01's text) rather
than restating the ladder.

## Touch

Do NOT touch `.claude/agents/critic.md`, `.claude/skills/critique/SKILL.md`
(task 03), `.claude/agents/verifier.md` (task 04), or any `antigravity/`
path (task 06).

## Steps

1. Read task 01's landed doctrine section, then the anchoring step in
   idea/SKILL.md (step 4) and breakdown's acceptance-authoring guidance.
2. Extend idea's anchoring step: classify each criterion's ladder level;
   deepest feasible wins; all-L0/L1 requirements get a `Depth ceiling:`
   annotation naming the behavioral complement — cite the memory doc.
3. Mirror the same rule into breakdown's acceptance-authoring text
   (its existing version-bump/mirror guidance stays as-is).
4. idea/SKILL.md is ultra-gated: run `bash evals/lint-ultra-gate.sh`
   before committing.

## Acceptance

- [ ] `grep -c 'depth ceiling' .claude/skills/idea/SKILL.md` → ≥ 1 and
      `grep -c 'depth ceiling' .claude/skills/breakdown/SKILL.md` → ≥ 1
      and `grep -c 'ladder level' .claude/skills/idea/SKILL.md` → ≥ 1 and
      `grep -c 'ladder level' .claude/skills/breakdown/SKILL.md` → ≥ 1
      (all four 0 today, verified 2026-07-19). Depth ceiling: prose
      authoring instruction — behavioral complement is the idea-evalset
      adversarial scenario owned by specs/eval-coverage-tiers, plus a
      manual-pending human read of the edited sections.
- [ ] `bash evals/lint-ultra-gate.sh` → exit 0

## Progress

- 2026-07-19: session wind-down at maintainer wrap-up request; worker died in a harness reconnect before any commit or verdict (branch at dispatch base, nothing to rescue). Not a failed attempt. Reset to pending for the next /drain run.
