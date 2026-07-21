# Task 02: drain reference.md — Blocks: derivation per HUMAN.md filing row

Status: done
Depends on: none
Priority: P1
Budget: 20 turns
Spec: ../SPEC.md (requirements R3, R4)
Touch: .claude/skills/drain/reference.md

## Goal

`.claude/skills/drain/reference.md`'s "HUMAN.md filing (R2)" section
states, per row of its six-row mapping table, how the newly-added
`Blocks:` clause is derived: a mechanical `Depends on:` task-name
derivation (citing SKILL.md step 2's "unblocking-power" computation) for
the four dependency-bearing rows, and a literal fixed phrase for the two
non-dependency rows.

## Touch

Only `.claude/skills/drain/reference.md`. Do not touch
`.claude/rules/human-blockers.md` (task 01), `HUMAN.md` (task 03), or
`antigravity/.agents/workflows/drain.md` (task 04) — Touch-disjoint, no
shared design decision.

## Steps

1. Read the "HUMAN.md filing (R2)" section (~line 1718 onward) and its
   six-row mapping table.
2. Add, adjacent to the table (or per-row), the `Blocks:` derivation rule
   per SPEC.md's Solution section:
   - Dependency-bearing rows ("Deferred questions still unanswered",
     "`Contradicts-premise` deferred", "`Unblock: ask:` blocked tasks",
     "`Unblock: run:` blocked tasks"): derive the blocked-task name set
     from the same lookup `/drain`'s SKILL.md step 2 dispatch tie-break
     computes ("count of still-`pending` tasks whose `Depends on:` names
     this task, resolved as the dispatchability check does" —
     `.claude/skills/drain/SKILL.md:130`) — cite it by name
     ("unblocking-power"), expose the underlying task-name set rather than
     just the count, and render `Blocks:` from those names (or "Blocks: no
     other pending task" when empty).
   - Fixed-phrase rows, verbatim: "Decision-shaped or gate-refused stubs"
     → `Blocks: promotion of this stub to a dispatchable task`; "NOT-READY
     specs (critique intake)" → `Blocks: breakdown of this spec into
dispatchable tasks`.
3. Keep the existing table and its six checklist-source rows intact —
   this task adds the derivation guidance, it does not change the
   `ask|run|provision|decide` type mapping.

## Acceptance

- [x] `grep -c 'promotion of this stub to a dispatchable task' .claude/skills/drain/reference.md` → 1
      (verifier: → 1; stub-row fixed phrase rendered in the 2-row table)
- [x] `grep -c 'breakdown of this spec into dispatchable tasks' .claude/skills/drain/reference.md` → 1
      (verifier: → 1; NOT-READY-spec-row fixed phrase in the same table)
- [x] `sed -n '/^## HUMAN.md filing (R2)/,/^## /p' .claude/skills/drain/reference.md | grep -c 'unblocking-power'` → ≥ 1
      (verifier: → 1, match inside the "HUMAN.md filing (R2)" section
      (heading at reference.md:1890), citing SKILL.md step 2's
      unblocking-power computation by name)
      (behavioral complement: verifier confirmed the derivation rule's
      SKILL.md:130 citation is accurate; no live `Unblock: ask:`/`run:`
      blocked task exists in specs/, so the by-hand application was
      vacuous per the depth-ceiling instruction, judged coherent)
      evidence: specs/human-blocker-impact-clarity/evidence/02-drain-reference-derivation.md
- Depth ceiling (covers the three checks above): L0/L1 on skill-reference
  prose — the two fixed phrases are themselves pinned verbatim by the
  spec, so text-presence is most of the requirement. Behavioral
  complement: a named verifier judgment instruction — the verifier picks
  one real `Unblock: ask:`- or `Unblock: run:`-blocked task in this
  repo's `specs/`, applies the documented derivation, and confirms the
  derived `Blocks:` task-name set matches the tasks whose `Depends on:`
  actually name it (or "no other pending task" when none do).

## Decisions

- Refreshed the inline entry-grammar copy line in the "HUMAN.md filing (R2)"
  section (`<one-line action>` → `<plain-language action> — Blocks: <impact>`)
  so the illustrative example stays consistent with the `Blocks:` derivation
  guidance this task adds and with task 01's already-landed grammar in
  human-blockers.md. Reversible default: not required by any acceptance
  criterion; stays inside the Touch-scoped file. Reverse by restoring the
  line to `- [ ] <ISO date> · <source path> · <type> — <one-line action>`.
