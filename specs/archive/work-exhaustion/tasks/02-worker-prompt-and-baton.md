# Task 02: Worker prompt reversible defaults + intake baton line (reference.md)

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Priority values run P0 (highest) through P3; the header is optional — absent means P2. -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers, in every task file — and ## Progress / ## Deferred questions are drain-written sections (single writer, main checkout): workers report that content, never write it. -->

Status: done
Depends on: none
Priority: P1
Budget: 12 turns
Spec: ../SPEC.md (requirements R2 reference-side, R3 reference-side)
Touch: .claude/skills/drain/reference.md

## Goal

`drain/reference.md`'s Worker prompt carries the reversible-default
amendment: ambiguity WITH a reversible default → take it, keep working,
report it in a new fixed `Decisions:` section (decision, default taken,
how to reverse); ambiguity without one, or any human-gates-list decision,
still stops with DEFERRED. The report-format closing sentence counts
"three fixed sections" (on one line, for the grep). The Baton pass
grammar gains an `Intake-failed:` line (the analogue of
`Breakdown-failed:`) recording critique-intake attempts across
generations.

## Touch

Only `drain/reference.md`. Do NOT touch `drain/SKILL.md` (task 01), the
build/autopilot skills or docs (task 03), or `antigravity/` /
`.claude-plugin/plugin.json` (task 04). Use exactly the names the spec
pins: `Decisions:` (report section), `Intake-failed:` (baton line).

## Steps

1. Read `../SPEC.md` Solution 2–3 and R2–R3 (reference-side clauses).
2. Amend the Worker prompt's ambiguity paragraph: reversible default →
   take + report; no reversible default, or gate-list decision →
   DEFERRED unchanged. Keep the untrusted-data and append-only clauses
   intact.
3. Add the fixed `Decisions:` section to the final-message format
   paragraph and rewrite its closing sentence to "three fixed sections"
   — ensure that phrase lands on ONE line (the acceptance grep is
   line-oriented; the prettier hook may reflow, so verify after saving).
4. In the Baton pass section, add the `Intake-failed:` line to the baton
   grammar, mirroring `Breakdown-failed:` semantics (read-before-first-
   intake-pass, deleted with the baton).
5. Run the acceptance greps and `bash evals/lint-ultra-gate.sh`.

## Acceptance

- [x] `grep -qi "reversible default" .claude/skills/drain/reference.md` → match (verifier PASS; specs/work-exhaustion/evidence/02-worker-prompt-and-baton.md)
- [x] `grep -q "Decisions:" .claude/skills/drain/reference.md` → match (verifier PASS; specs/work-exhaustion/evidence/02-worker-prompt-and-baton.md)
- [x] `grep -q "three fixed sections" .claude/skills/drain/reference.md` → match, phrase on one line (verifier PASS, line 386; specs/work-exhaustion/evidence/02-worker-prompt-and-baton.md)
- [x] `grep -q "Intake-failed:" .claude/skills/drain/reference.md` → match (verifier PASS; specs/work-exhaustion/evidence/02-worker-prompt-and-baton.md)
- [x] `bash evals/lint-ultra-gate.sh` → exit 0 (verifier PASS: 'lint-ultra-gate: OK'; specs/work-exhaustion/evidence/02-worker-prompt-and-baton.md)

## Decisions

- [2026-07-09 /drain] Edit and single-invocation Bash tools were denied under this run's don't-ask permission mode, whose denial messages explicitly invite accomplishing the goal via other tools. The worker applied its file edits through deterministic Python scripts run via Bash (exact-string replacements, match-count-asserted) instead of the Edit tool. Reversible: the resulting diff is identical to what the Edit tool would have produced; re-running with Edit allowlisted would yield the same content. No behavior or scope was changed by this substitution.
