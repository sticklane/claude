# Task 03: VCS-agnostic prose rewrite — critique, fleet, concurrent-sessions, gate

Status: in-progress
Depends on: none
Priority: P2
Budget: 20 turns
Spec: ../SPEC.md (requirements R1, R2, R5, R6; decisions 1, 3)
Touch: .claude/skills/critique/SKILL.md, .claude/skills/fleet/SKILL.md, .claude/rules/concurrent-sessions.md, .claude/skills/gate/SKILL.md, .claude/skills/gate/reference.md, antigravity/.agents/workflows/critique.md, antigravity/.agents/skills/gate/SKILL.md, antigravity/.agents/skills/gate/reference.md

## Goal

`critique/SKILL.md`, `fleet/SKILL.md`, and
`.claude/rules/concurrent-sessions.md` describe VCS actions in intent-level
language per decision 1 (R1, R2). `gate/SKILL.md` explicitly states its
pre-commit-hook installation mechanism is git-specific and that
non-colocated jj repos need a different enforcement point (R5, decision 3,
no mechanism change). `gate/reference.md` gets a one-line note that its
`.git/*` glob and `git push` deny-pattern are git-specific pattern strings
(R5, no pattern change). Mirrors updated in the same commit per R6:
`antigravity/.agents/workflows/critique.md` (only if the rewrite here
introduces a mismatch with its already-0-git-hit content — verify, don't
assume an edit is needed), `antigravity/.agents/skills/gate/SKILL.md` (no
git-hook callout needed there — different, harness-native hook mechanism,
per decision 3), `antigravity/.agents/skills/gate/reference.md` (same R5
pattern-string note as the Claude Code copy). `concurrent-sessions.md` has
no antigravity counterpart (R6) — no mirror edit for it.

## Touch

This task owns exactly these five `.claude/` files and their three listed
mirror touchpoints. Do not touch drain, build/breakdown/onboard/autopilot,
or any agents/*.md file — those belong to sibling tasks.

## Steps

1. Read all five `.claude/` files.
2. `critique/SKILL.md` and `fleet/SKILL.md`: apply decision 1's rewrite (1
   hit each per the spec's inventory).
3. `.claude/rules/concurrent-sessions.md` (R2): reword the pre-flight
   collision checks as VCS-agnostic intent ("check for another checkout of
   this worktree", "check for unexplained working-tree changes"), keeping
   `git worktree list`/`git status` only as a labeled example.
4. `gate/SKILL.md` (R5): add an explicit callout that the pre-commit hook it
   installs is git-specific and non-colocated jj repos need a different
   enforcement point. No mechanism change.
5. `gate/reference.md` (R1 + R5): apply decision 1's rewrite to any other
   git-command prose, and add a one-line note next to the `.git/*` glob and
   `git push` deny-pattern that these are git-specific pattern strings, not
   VCS-agnostic. No pattern change.
6. Check `antigravity/.agents/workflows/critique.md` for git hits; if still
   0 and no mismatch is introduced by step 2's edit, leave it untouched (per
   R6's note) — do not manufacture a needless mirror edit.
7. Edit `antigravity/.agents/skills/gate/SKILL.md`: confirm no git-hook
   callout is needed (it already uses a harness-native hook mechanism per
   decision 3) — apply ordinary decision-1 rewriting to any other git
   mentions found there.
8. Edit `antigravity/.agents/skills/gate/reference.md`: add the same
   git-specific pattern-string note next to its `.git/*` glob / `git push`
   deny pattern.

## Acceptance

- [ ] `rg -Un --pcre2 '`git[^`]*`' .claude/skills/critique/SKILL.md .claude/skills/fleet/SKILL.md` —
      every hit labeled "e.g., under git:" or removed.
- [ ] `grep -n 'git worktree list\|git status' .claude/rules/concurrent-sessions.md` —
      any remaining hits are inside a labeled example, preceded by
      intent-level phrasing.
- [ ] `grep -n 'git-specific\|pre-commit hook' .claude/skills/gate/SKILL.md` —
      shows the limitation callout.
- [ ] `grep -n 'git-specific' .claude/skills/gate/reference.md antigravity/.agents/skills/gate/reference.md` —
      shows the pattern-string note in both copies.
