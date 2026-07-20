# Task 06: Rewire live /drain to invoke admission.py

Status: in-progress
Depends on: 01, 04, specs/drain-frontier-scanner/tasks/02-drain-consumes-scanner.md
Priority: P1
Budget: 10 turns
Spec: ../SPEC.md (requirement R15)
Touch: .claude/skills/drain/SKILL.md, .claude/skills/drain/reference.md

## Goal

Rewire live `/drain` execution on Claude Code to invoke `admission.py`
(task 04) for the two checks it now owns: spec-lease claim eligibility (R1)
and the cross-spec/two-level cap decision (R2) — replacing the
hand-executed prose version of those two checks specifically. The same-spec
rolling-window mechanics (`Group:` lines, per-task Touch-disjointness within
one already-claimed spec) are unchanged and stay prose-driven, exactly as
today.

This task depends on `specs/drain-frontier-scanner`'s task 02
(`.claude/skills/drain/{SKILL.md,reference.md}` consuming `drain_frontier.py`)
because both tasks edit the same step-1 admission prose in the same two
files — they must land in sequence, never as concurrent conflicting edits.
Read that task's landed diff before starting so this task's edits build on
top of it rather than reverting or duplicating its `drain_frontier.py`
invocation instructions.

## Touch

Only `.claude/skills/drain/SKILL.md` and `.claude/skills/drain/reference.md`.
Do not touch `admission.py` itself (task 04's scope, already merged) or
`drain_frontier.py` (owned by `specs/drain-frontier-scanner`).

## Steps

1. Read `specs/drain-frontier-scanner/tasks/02-drain-consumes-scanner.md`'s
   landed diff to SKILL.md/reference.md in full, and task 04's landed
   `admission.py` interface — this task's edits must compose with both, not
   conflict with either.
2. Rewrite SKILL.md's step-1 owner-lease claim procedure (currently prose
   describing the widened cross-spec admission model per task 01) to
   instruct the agent to run `admission.py` by path, mirroring
   `.claude/skills/prioritize/SKILL.md:35`'s exact phrasing convention
   ("run `python3 <this skill dir>/admission.py <args>`"). Keep the
   invocation instruction itself short — supporting detail (exact CLI args,
   output schema, error handling) goes in reference.md, per R9's ≤500-line
   SKILL.md budget (already tight after task 01: 495 lines, ~5 lines of
   slack).
3. Extend reference.md's "Rolling-window admission & merge" section (or
   wherever task 01 landed the cross-spec admission prose) with
   `admission.py`'s full invocation contract: what arguments it takes, what
   it returns, and how the agent should act on a non-zero exit (treat as a
   claim failure, not a crash to work around).
4. Confirm the same-spec rolling-window mechanics (`Group:` lines,
   per-task Touch-disjointness within one claimed spec) are explicitly
   UNCHANGED and still prose-driven — do not accidentally fold them into
   `admission.py`'s scope; that module owns only spec-claim eligibility and
   the two-level cap (R14).
5. Run `wc -l .claude/skills/drain/SKILL.md` after edits; if over 500,
   relocate additional body content to reference.md until it's back at or
   under budget, per R9 (this task must not reopen that budget violation).

## Acceptance

- [ ] `grep -c "admission.py" .claude/skills/drain/SKILL.md
  .claude/skills/drain/reference.md` → combined count ≥ 2 (currently 0
      in both, verified 2026-07-19)
- [ ] `wc -l < .claude/skills/drain/SKILL.md` → ≤ 500
- [ ] A verifier reads SKILL.md's step-1 prose and confirms it instructs the
      agent to invoke `admission.py` for spec-lease claim and cross-spec cap
      decisions specifically (not the same-spec `Group:`/Touch-disjointness
      rolling-window logic, which stays prose-driven) — an L0 grep for the
      filename cannot distinguish "mentioned" from "correctly scoped to the
      right two checks."
- [ ] Every project gate this repo runs at merge time (`specs/status.sh`,
      `claude plugin validate .`, every `tests/test_*.sh`,
      `./bin/check-agent-model-pins`, `evals/lint-ultra-gate.sh`,
      `evals/lint-skill-size-gate.sh`) exits 0 after the change lands.
