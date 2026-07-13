# Task 01: Intake-refused lines + assessor must-author contract

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers. -->

Status: done
Depends on: none
Priority: P1
Budget: 6 turns
Spec: ../SPEC.md (requirements R1, R3, R4)
Touch: .claude/skills/drain/SKILL.md, .claude/skills/drain/reference.md

## Goal

Per SPEC R1/R3/R4: every non-promotion stub-intake outcome writes
`Intake-refused: <screen|assess|gate> — <reason> (<date>)` immediately
after Status: (drain-written; cleared by a later PASS/OBSOLETE Act write
in the same commit, extending the Original-report strip clause); exit
checklist section 6 quotes it. The assessor contract gains: ACTIONABLE
requires authored criteria+Touch+Budget — it "may not return
ACTIONABLE-without-criteria"; the only other outcomes are DECISION-SHAPED
(decision named) or OBSOLETE (evidence cited), each producing an R1 line.
reference.md's stub-intake section cites the three 2026-07-11 stubs
(cache-reprime-visibility/tasks/05, agentprof-attribution-gaps/tasks/07,
/08) as worked authoring examples. NOTE: drain SKILL.md is ultra-path —
run `bash evals/lint-ultra-gate.sh` before committing.

## Acceptance

- [x] `grep -qi 'Intake-refused' .claude/skills/drain/SKILL.md && grep -qi 'Intake-refused' .claude/skills/drain/reference.md` → hits (0 today, verified) — verifier: both hit, exit 0 (evidence/01-intake-contract.md)
- [x] `grep -qi 'may not return ACTIONABLE-without-criteria' .claude/skills/drain/reference.md` → hit (0 today) — verifier: matched reference.md:1025
- [x] `grep -c '2026-07-11' .claude/skills/drain/reference.md` ≥ 1 AND MANUAL: three stubs cited as worked examples; lifecycle clear-on-promotion stated — verifier: count 7; "R4 — worked authoring examples (2026-07-11)" cites tasks/05, /07, /08; clear-on-promotion stated
- [x] `bash evals/lint-ultra-gate.sh` → OK — verifier: "OK — all ultra mentions gated in 4 files", exit 0
