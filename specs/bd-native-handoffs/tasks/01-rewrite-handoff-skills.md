# Task 01: Rewrite handoff and resume-handoff skills to be bd-native

Status: pending
Depends on: none
Priority: P2
Budget: 25 turns
Spec: ../SPEC.md (requirements R1, R2, R4, R9)
Touch: .claude/skills/handoff/SKILL.md, .claude/skills/resume-handoff/SKILL.md, specs/structured-handoff-headers/SPEC.md

## Goal

`.claude/skills/handoff/SKILL.md` no longer writes `HANDOFF.md`; it parks
session state as bd issue comments plus one lightweight `handoff`-labeled
bd issue, per SPEC.md's Solution section. `.claude/skills/resume-handoff/
SKILL.md` locates and resumes that bd-native state instead of finding
files. `specs/structured-handoff-headers/SPEC.md` carries a superseded
notice.

## Steps

1. Read `.claude/skills/handoff/SKILL.md` and `.claude/skills/resume-
   handoff/SKILL.md` in full (both are short, ~100 lines each).
2. Read `docs/external-playbooks.md` lines 513-519 for the exact
   superseded-notice blockquote format this repo already uses.
3. Rewrite `.claude/skills/handoff/SKILL.md` per SPEC.md's R1: check bd
   usability first (`bd list --json`); if unusable, tell the user and
   point at `agentic init` / `bd init --non-interactive --remote ""
   --skip-agents`, then stop — no file, no silent fallback. When bd is
   usable: for every touched/open bd issue, `bd comment <id> "..."` with
   its session-state update; create one new issue
   (`bd create "Session handoff: <topic>" --labels handoff --type=task
   --design "..." --notes "..."`); link it to every touched issue
   (`bd dep add <handoff-id> <touched-id> -t tracks`); keep the existing
   verifier-before-parking step (unchanged behavior, just record the
   verdict via `--notes` instead of a file section); close by telling the
   user `/clear` then `/resume-handoff`.
4. Rewrite `.claude/skills/resume-handoff/SKILL.md` per SPEC.md's R2:
   locate via `bd list --label handoff --status=open --json`; zero found
   → nothing to resume, stop; multiple found → `AskUserQuestion` built
   from each issue's title + a bounded `bd show <id>` read (not full
   comment history); once resolved, `bd show <id> --json
   --include-comments` plus each `tracks`-linked issue's latest comment;
   resume the recorded next step with the same `/build`/`/drain` gating
   as today; `bd close <handoff-id> --reason "resumed and consumed"` once
   captured — tracked work issues stay open.
5. Add the superseded-notice blockquote to the top of
   `specs/structured-handoff-headers/SPEC.md` (above its first `##`),
   matching the `docs/external-playbooks.md:515-519` format, noting the
   compact-header technique it added has no file to attach to now.

## Acceptance

- [ ] `grep -ci "HANDOFF.md" .claude/skills/handoff/SKILL.md` → 0
- [ ] `grep -c "bd comment\|bd create.*--labels handoff\|bd dep add.*-t tracks" .claude/skills/handoff/SKILL.md` → ≥ 3
- [ ] `grep -c "agentic init\|bd init" .claude/skills/handoff/SKILL.md` → ≥ 1
- [ ] `grep -ci "HANDOFF.md" .claude/skills/resume-handoff/SKILL.md` → 0
- [ ] `grep -c "bd list --label handoff\|bd show.*--include-comments\|bd close.*resumed and consumed" .claude/skills/resume-handoff/SKILL.md` → ≥ 3
- [ ] `grep -c "^Superseded\|Superseded (" specs/structured-handoff-headers/SPEC.md` → ≥ 1
- [ ] `find /Users/sjaconette/claude -iname "HANDOFF*.md" -not -path "*/.git/*"` → empty
