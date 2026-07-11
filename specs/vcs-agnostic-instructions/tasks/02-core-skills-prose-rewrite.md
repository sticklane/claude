# Task 02: VCS-agnostic prose rewrite — build, breakdown, onboard, autopilot

Status: in-progress
Depends on: none
Priority: P2
Budget: 24 turns
Spec: ../SPEC.md (requirements R1, R6; decisions 1, 5)
Touch: .claude/skills/build/SKILL.md, .claude/skills/breakdown/SKILL.md, .claude/skills/onboard/SKILL.md, .claude/skills/autopilot/reference.md, antigravity/.agents/workflows/build.md, antigravity/.agents/skills/breakdown/SKILL.md, antigravity/.agents/skills/onboard/SKILL.md, antigravity/.agents/workflows/autopilot.md

## Goal

`build/SKILL.md`, `breakdown/SKILL.md`, `onboard/SKILL.md`, and
`autopilot/reference.md` describe VCS actions in intent-level language per
decision 1 — including `breakdown/SKILL.md`'s `git show
<base-commit>:<path> | grep version` example at line 98 (R1's explicit
callout) — with `autopilot/reference.md:23-28`'s
`permissions.allow`/`deny` JSON block (decision 5) left untouched. Each
file's antigravity mirror gets the matching edit in the same commit.

## Touch

This task owns exactly these four `.claude/` files and their four listed
mirrors. Do not touch drain, gate, critique, fleet, concurrent-sessions.md,
or any agents/*.md file — those belong to sibling tasks.

## Steps

1. Read all four `.claude/` files.
2. Apply decision 1's rewrite: replace git-command syntax with intent-level
   phrasing, keeping VCS nouns as vocabulary; label any kept concrete
   example ("e.g., under git: ...").
3. For `breakdown/SKILL.md` line 98's `git show <base-commit>:<path> | grep
   version` example specifically: reframe as a labeled git example (the
   underlying concept — "compare a path's content at the task's base commit
   against its current value" — is what the acceptance criterion actually
   requires; keep the git syntax as one labeled worked example under it).
4. For `autopilot/reference.md`, leave the `permissions.allow`/`deny` JSON
   block (lines ~23-28) exactly as written — decision 5 exemption; prose
   immediately around it may note the grant is git-specific.
5. Apply the same rewrite to each antigravity mirror:
   `antigravity/.agents/workflows/build.md`,
   `antigravity/.agents/skills/breakdown/SKILL.md`,
   `antigravity/.agents/skills/onboard/SKILL.md`,
   `antigravity/.agents/workflows/autopilot.md` (preserving its own
   equivalent permission-grant exemption per R6).
6. Re-run the detector command below on each `.claude/` file and fix any
   remaining unlabeled hits.

## Acceptance

- [ ] `rg -Un --pcre2 '`git[^`]*`' .claude/skills/build/SKILL.md .claude/skills/breakdown/SKILL.md .claude/skills/onboard/SKILL.md .claude/skills/autopilot/reference.md` —
      every hit's starting line contains "e.g., under git:" or is the named
      `autopilot/reference.md` permissions block exemption.
- [ ] `grep -n 'git show' .claude/skills/breakdown/SKILL.md` shows the line
      now labeled as a git example, not the sole phrasing.
- [ ] `git diff --stat antigravity/.agents/workflows/build.md antigravity/.agents/skills/breakdown/SKILL.md antigravity/.agents/skills/onboard/SKILL.md antigravity/.agents/workflows/autopilot.md` —
      all four mirrors show a non-empty diff.
