# Task 06: Reword global CLAUDE.md files and antigravity README

Status: done
Depends on: none
Priority: P3
Budget: 8 turns
Spec: ../SPEC.md (requirements R8, R9)
Touch: /Users/sjaconette/CLAUDE.md, /Users/sjaconette/.claude/CLAUDE.md, antigravity/README.md

## Goal

The two global user CLAUDE.md files' one git-specific line each ("the git
pre-commit hook ... bypass with `--no-verify`") is reworded to intent-level
phrasing ("the VCS's pre-commit hook") — R8, courtesy pass, not gated on
this repo's acceptance criteria since those files live outside it.
`antigravity/README.md`'s one-line install instruction (`git add .agents
AGENTS.md && git commit -m "..."`) is reworded to intent-level phrasing —
R9.

## Touch

This task owns exactly these three files, two of which are outside this
repo. Do not touch any other file.

## Steps

1. Read `/Users/sjaconette/CLAUDE.md` and `/Users/sjaconette/.claude/CLAUDE.md`;
   locate the "git pre-commit hook ... `--no-verify`" line in each.
2. Reword each to intent-level phrasing (e.g. "the VCS's pre-commit hook ...
   bypass with the VCS-appropriate flag"), keeping `--no-verify` as a
   labeled git example if useful.
3. Read `antigravity/README.md`; locate the `git add .agents AGENTS.md &&
   git commit -m "..."` install instruction.
4. Reword to intent-level phrasing (e.g. "commit the `.agents` directory and
   `AGENTS.md` to your repo").

## Acceptance

- [x] `grep -n 'git pre-commit hook' /Users/sjaconette/CLAUDE.md /Users/sjaconette/.claude/CLAUDE.md` —
      returns no hits.
- [x] `grep -n 'git add .agents\|git commit -m' antigravity/README.md` —
      returns no hits.
