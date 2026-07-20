# Task 02: token-discipline.md swarm-mode carve-out

Status: pending
Depends on: none
Priority: P2
Budget: 4 turns
Spec: ../SPEC.md (requirement R3)
Touch: .claude/rules/token-discipline.md

## Goal

`.claude/rules/token-discipline.md`'s existing "cap the fleet at a 3–5
concurrent-writer window" rule gains an explicit carve-out sentence
authorizing drain's raised ≤10 total-worker cap for multi-spec swarm mode,
citing `specs/drain-multi-spec-swarm` by slug, so the raised cap is a
documented exception rather than a silent doctrine violation.

## Touch

Only `.claude/rules/token-discipline.md`. Do not touch
`.claude/skills/drain/SKILL.md` or `.claude/skills/drain/reference.md`
(task 01's scope).

## Steps

1. Read ../SPEC.md's R3 and the "cap the fleet at a 3–5 concurrent-writer
   window" rule in `.claude/rules/token-discipline.md`.
2. Add one carve-out sentence naming drain's multi-spec swarm mode,
   the raised ≤10 cap, and citing `specs/drain-multi-spec-swarm` — placed
   adjacent to the existing 3–5 window rule so a reader sees both together.

## Acceptance

- [ ] `grep -ci "swarm.*10\|10.*swarm\|drain-multi-spec-swarm" .claude/rules/token-discipline.md` → ≥ 1
      (0 today, verified 2026-07-19). Depth ceiling: L0 grep on doctrine
      prose — the honest ceiling for a one-sentence rule edit. Behavioral
      complement, a named verifier judgment: confirm the carve-out
      sentence sits adjacent to the existing "3–5 concurrent-writer
      window" rule and cites `specs/drain-multi-spec-swarm` by slug — not
      merely that the pattern matches somewhere in the file.
