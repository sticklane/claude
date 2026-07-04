# Task 01: "Dispatch authoring" rule section + CLAUDE.md bullet

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
Status: done
Depends on: none
Priority: P1
Budget: 25 turns
Spec: ../SPEC.md (requirements R1, R2)
Touch: .claude/rules/token-discipline.md, CLAUDE.md, antigravity/AGENTS.md

## Goal

`.claude/rules/token-discipline.md` gains a "Dispatch authoring" section
stating, each in 1–2 lines with a citation into the research docs:
(a) tier-by-stage-type; (b) subagent returns capped at 1–2k tokens;
(c) evaluator loops bounded 2–4 cycles, skipped when a deterministic
check exists; (d) single-call rubric judge default; (e) the
deterministic-vs-model-driven placement axis; (f) effort-scaling dispatch
language. CLAUDE.md's Authoring conventions gain exactly one pointer
bullet. The antigravity AGENTS.md mirrors the section per the existing
token-discipline mirroring pattern.

## Touch

Must NOT touch: any SKILL.md (task 03 retrofits them), bin/ or tests/
(task 02), .claude/workflows/ (task 04), plugin.json (task 05).

## Steps

1. Confirm acceptance greps fail (RED).
2. Write the six-point section, citations only — no restated research.
3. Add the single CLAUDE.md bullet; mirror the section to
   antigravity/AGENTS.md.
4. Run acceptance.

## Acceptance

- [x] `grep -q "Dispatch authoring" .claude/rules/token-discipline.md` → exit 0; section has all six points, each with a citation into docs/orchestration-research-2026-07.md, docs/context-management-research-2026-07.md, or docs/anthropic-playbook.md — verifier confirmed all six points present and every cited anchor resolves (evidence/01-dispatch-authoring-rule.md)
- [x] `grep -c "Dispatch authoring" CLAUDE.md` → 1 (one pointer bullet, no restated content) — verifier confirmed count 1 and pointer-only (evidence/01-dispatch-authoring-rule.md)
- [x] `grep -q "Dispatch authoring" antigravity/AGENTS.md` → exit 0 — verifier confirmed exit 0, mirror follows existing self-contained pattern (evidence/01-dispatch-authoring-rule.md)
