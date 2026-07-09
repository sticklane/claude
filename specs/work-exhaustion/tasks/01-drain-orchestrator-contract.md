# Task 01: Drain orchestrator exhaustion contract (SKILL.md)

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Priority values run P0 (highest) through P3; the header is optional — absent means P2. -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers, in every task file — and ## Progress / ## Deferred questions are drain-written sections (single writer, main checkout): workers report that content, never write it. -->

Status: done
Depends on: none
Priority: P1
Budget: 20 turns
Spec: ../SPEC.md (requirements R1, R2 SKILL-side, R3 SKILL-side, R4 drain-side, R5)
Touch: .claude/skills/drain/SKILL.md

## Goal

`drain/SKILL.md` carries the session-level exhaustion contract from the
spec's Solution 1–5: never end while dispatchable work remains in the
launched scope (no-arg = all of `specs/`, one spec at a time under the
release-on-nothing-left-to-dispatch lease discipline); a "critique
intake" branch at the exhaustion trigger, evaluated before 3b; drain-side
decision recording (append worker-reported `Decisions:` entries to the
task file's `## Decisions`; gate-list decisions route through DEFERRED to
the batch interview, never `Status: blocked`); the six-section exit
checklist fused with the batch interview, once per session at scope
exhaustion; and the /handoff escape scoped to generations-cap exhaustion,
baton first.

## Touch

Only `drain/SKILL.md`. Do NOT touch `drain/reference.md` (task 02 owns
the worker prompt and baton grammar — cite its pinned names:
`Decisions:` report section, `Intake-failed:` baton line), nor
build/autopilot skills (task 03), nor `docs/human-gates.md` (task 03),
nor `antigravity/` or `.claude-plugin/plugin.json` (task 04).

## Steps

1. Read `../SPEC.md` Solution 1–5 and R1–R5 (SKILL-side clauses only).
2. Step 1/2 text: state the exhaustion contract and the no-arg
   sequential-walk lease discipline (release when a spec has nothing
   left to dispatch; re-claim on interview-answer re-dispatch;
   transient 3b/intake lease overlap allowed).
3. Add the "critique intake" branch to the exhaustion trigger,
   immediately before 3b: eligibility (no `tasks/`, no
   `Breakdown-ready:` header), lease claim → /critique → release,
   once per run across generations via the `Intake-failed:` baton line
   (cite reference.md; do not edit it).
4. Step 3 verdict handling: append worker `Decisions:` entries to the
   task file under `## Decisions`; state that gate-list decisions arrive
   as DEFERRED and join the batch interview, and that `Status: blocked`
   stays failures-only.
5. Step 3a: name /handoff as the escape when the generations cap is
   exhausted — baton first, /handoff only past the cap.
6. Step 4: fuse the exit checklist with the batch interview — six fixed
   sections (unanswered deferred questions, defaults taken, blocked
   items, NOT-READY specs, draft stubs awaiting promotion, next
   commands), each entry with a file path; once per session.
7. Run the acceptance greps and `bash evals/lint-ultra-gate.sh` (drain
   is an ultra-path skill — keep every "ultra" mention within ±3 lines
   of the "active runtime profile" marker).

## Acceptance

- [x] `grep -qi "dispatchable work remains" .claude/skills/drain/SKILL.md` → match — Exhaustion contract para, SKILL.md opening (evidence/01-drain-orchestrator-contract.md, criterion 1 PASS).
- [x] `grep -qi "critique intake" .claude/skills/drain/SKILL.md` → match — new "## Critique intake" section between 3a and 3b (evidence file, criterion 2 PASS).
- [x] `grep -q "## Decisions" .claude/skills/drain/SKILL.md` → match — "Record decisions" subsection in step 3 (evidence file, criterion 3 PASS).
- [x] `grep -q "/handoff" .claude/skills/drain/SKILL.md && grep -qi "generations cap" .claude/skills/drain/SKILL.md` → both match, same passage — 3a max-generations-cap passage: "The baton is always the first escape … The /handoff escape applies only where the baton cannot: once this generations cap is exhausted" (evidence file, criterion 4 PASS, baton-first confirmed).
- [x] `grep -qi "checklist" .claude/skills/drain/SKILL.md` → match — six-section exit checklist in step 4 (evidence file, criterion 5 PASS).
- [x] `bash evals/lint-ultra-gate.sh` → exit 0 — "all ultra mentions gated in 4 files" (evidence file, criterion 6 PASS).

## Discovered

- Shrink drain/SKILL.md back under the 500-line convention (stub 05-shrink-drain-skill.md)
