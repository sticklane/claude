# Task 02: SKILL.md — stop implying naming is gen-1-only

Status: pending
Depends on: none
Priority: P2
Budget: 10 turns
Spec: ../SPEC.md (requirement R3)
Touch: .claude/skills/drain/SKILL.md

## Goal

`.claude/skills/drain/SKILL.md`'s "Gen-1 startup advisories" summary line
no longer states unqualified that naming fires "At gen-1 startup ONLY
(never on baton generations)" — it notes inline that naming has its own
precise trigger, not gen-1-restricted, pointing to reference.md for detail.

## Touch

Only `.claude/skills/drain/SKILL.md`. Do not touch
`.claude/skills/drain/reference.md` (task 01) or
`antigravity/.agents/workflows/drain.md` (task 03) — Touch-disjoint, no
shared design decision.

## Steps

1. Read the "Gen-1 startup advisories" paragraph (~line 50-57): "At gen-1
   startup ONLY (never on baton generations), drain runs three
   non-blocking advisories — **name the terminal tab**, **sweep foreign
   live sessions**, and print the **hub-economics** relaunch
   recommendations..."
2. Edit so naming carries an inline note that it is not gen-1-restricted
   (its own precise trigger lives in reference.md), while the other two
   advisories' gen-1-only framing is left unchanged. Keep the edit minimal
   — SKILL.md bodies point to reference.md for detail rather than
   restating it.

## Acceptance

- [ ] `grep -c "not gen-1-restricted" .claude/skills/drain/SKILL.md` → ≥ 1
