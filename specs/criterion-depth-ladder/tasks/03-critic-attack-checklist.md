# Task 03: Give the critic an acceptance-criteria attack checklist

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch, Rigor) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. -->

Status: pending
Depends on: 01
Priority: P2
Budget: 8 turns
Spec: ../SPEC.md (requirement R4)
Touch: .claude/agents/critic.md, .claude/skills/critique/SKILL.md

## Goal

The critic's spec-review charter gains the three-question
acceptance-criteria attack checklist (gameable-by-literal? anchor still
differs from disk? at least one L2+/ceiling-annotated check per
behavioral requirement?), with a gameable criterion lacking a depth
ceiling annotation blocking READY like an unmapped requirement.
critique/SKILL.md's triage gains the verbatim sentence "gameable
criteria are JUDGMENT-class, never MECHANICAL" inside its JUDGMENT
enumeration — placement matters; the MECHANICAL bullet's "under-scoped
acceptance command" must not be left claimable for gameability.

## Touch

Do NOT touch idea/breakdown SKILL.md (task 02), verifier.md (task 04),
or antigravity paths (task 06).

## Steps

1. Read task 01's doctrine section, critic.md's spec-review charter, and
   critique/SKILL.md's triage list.
2. Add the checklist to critic.md citing the memory doc; wire the
   blocks-READY force to the existing unmapped-requirement clause.
3. Insert the mandated verbatim sentence in critique/SKILL.md's JUDGMENT
   enumeration with the spec's rationale (spec-meaning change).
4. critique/SKILL.md is ultra-gated: run `bash evals/lint-ultra-gate.sh`
   before committing.

## Acceptance

- [ ] `grep -ci 'gameable' .claude/agents/critic.md` → ≥ 1 and
      `grep -c 'JUDGMENT-class, never MECHANICAL'
    .claude/skills/critique/SKILL.md` → ≥ 1 — the verbatim sentence
      encodes placement (both 0 today, verified 2026-07-19). Depth
      ceiling: prose charter — behavioral complement is task 05's eval
      scenario, which exercises the critic flagging a seeded gameable
      criterion.
- [ ] `bash evals/lint-ultra-gate.sh` → exit 0
