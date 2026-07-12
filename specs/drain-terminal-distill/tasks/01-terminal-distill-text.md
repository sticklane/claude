# Task 01: terminal distill in drain step 4 + distill unattended contract

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers. -->

Status: in-progress
Depends on: none
Priority: P1
Budget: 7 turns
Spec: ../SPEC.md (requirements R1, R2, R3)
Touch: .claude/skills/drain/SKILL.md, .claude/skills/distill/SKILL.md, antigravity/.agents/skills/distill/SKILL.md, CLAUDE.md

## Goal

Per SPEC R1/R2/R3: drain step 4 gains the terminal distill (Skill-tool
invocation of /distill after the exit checklist, at most once per
session, one-line announcement) replacing the ~600 conditional
suggestion; the ~648 closing line rewritten with "(self-chains per
conventions)" covering both terminal states; 3a gains only the one-line
pointer (cap path distills via step 4 — NO second insertion; ordinary
baton passes never distill). CLAUDE.md's self-chain bullet gains the
terminal-capture carve-out sentence. distill SKILL.md gains the
unattended-safe paragraph (adopt drain's where-available AskUserQuestion
idiom — distill has no interview today; judgment-needing learnings →
HUMAN.md `decide` entries per human-blockers-doc grammar; harvest
extends to run artifacts: Decisions/Progress entries, critique findings,
screen/sweep incidents, exit checklist); the antigravity distill port
gets the content-equivalent paragraph in the same commit. Ultra-path:
run `bash evals/lint-ultra-gate.sh` before committing. SEQUENCING: if
drain-wake-cost/04 (SKILL.md extraction) or human-blockers-doc/02 is
pending/in-progress, dispatch after they merge (Touch overlap
serializes mechanically).

## Acceptance

- [ ] `grep -qi 'terminal distill' .claude/skills/drain/SKILL.md` → hit AND MANUAL: once-per-session guard, ~648 rewrite, 3a pointer only, no second insertion
- [ ] `grep -qi 'terminal-capture' CLAUDE.md` → hit (0 today, verified)
- [ ] `grep -qi 'Agent-filed blockers' .claude/skills/distill/SKILL.md && grep -qi 'Agent-filed blockers' antigravity/.agents/skills/distill/SKILL.md` → hits (0 in both today)
- [ ] `bash evals/lint-ultra-gate.sh` → OK
