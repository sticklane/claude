# Task 13: the critique READY bar and finding contraction

<!-- Registration fields (Depends on, Budget, Touch, Rigor) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. Status and Priority are frozen authoring-time display only: bd owns their live values. -->

Status: pending
Depends on: 07
Priority: P2
Budget: 25 turns
Spec: ../SPEC.md (requirement EP16)
Touch: .claude/skills/critique/SKILL.md, evals/critique, tests/inventory/drain-economy-13.json

## Goal

`/critique`'s READY verdict gains one mechanical precondition — the spec's
acceptance block parses under the task 07 grammar and every criterion maps to
at least one requirement — and re-critique contracts instead of expanding: on a
second pass over the same spec the verdict evaluates resolution of the prior
findings only, and net-new findings route to the run report's Discovered digest
rather than back into the findings loop.

## Touch

Prose and eval fixtures only. This task must NOT change how findings are
mechanically applied or deduplicated — that is
`specs/critique-findings-loop-closure/`'s scope, and the spec draws the
boundary explicitly. It must not edit the grammar doc (task 07) or `bin/spec-gate`
(task 08); it cites the grammar as a gate on the verdict.

## Steps

1. Add the parse precondition to the READY verdict in
   `.claude/skills/critique/SKILL.md`: READY requires the acceptance block to
   parse under `docs/memory/acceptance-block-grammar.md` with each criterion
   mapping to ≥1 requirement; a non-parsing block is NOT READY citing the
   grammar by name, so the author knows what to fix.
2. Add the read-only precondition alongside it: a criterion that mutates bd,
   the working tree, or any live surface is NOT READY. This is the *only*
   enforcement point for D12 — `bin/spec-gate` executes what it is handed and
   does not sandbox it — so state the consequence, not just the rule.
3. Add the contraction rule for re-critique: same spec, second pass → evaluate
   resolution of prior findings only; net-new findings go to the digest with
   enough context to act on, never into the findings file.
4. Author an eval scenario under `evals/critique/` with three fixtures: a spec
   whose acceptance block does not parse (expect NOT READY citing the grammar);
   a spec whose block parses but whose criterion mutates live state (expect NOT
   READY citing the read-only rule); and a re-critique fixture carrying prior
   findings plus one net-new observation (expect the verdict scoped to the
   prior findings and the new observation in the digest).
5. Register the new scenario in the test inventory and confirm
   `evals/lint-eval-coverage.sh` still passes.

## Acceptance

- [ ] `grep -c 'acceptance-block grammar' .claude/skills/critique/SKILL.md` → ≥ 1
      (verified 0 today, 2026-07-30), and the READY section is the section it
      lands in — confirmed by an `awk` range over that section returning the
      same match. **L0** — Depth ceiling: a verdict rule is a model
      instruction; its behavioral complement is the NOT-READY eval fixture
      below.
- [ ] `bash evals/lint-eval-coverage.sh` → passes with the new scenario
      registered. **L2**
- [ ] `ls evals/critique/*/ -d | wc -l` → increased by 1 against the pre-task
      count recorded in this task's commit message. **L1**
- [ ] `bash evals/run.sh critique` → the new scenarios pass. **L3** —
      `manual-pending`: paid headless session; a human runs it and records the
      result (`docs/memory/unattended-worker-tool-limits.md`).
- [ ] `bash scripts/check.sh` → `check.sh: green`. **L2**
