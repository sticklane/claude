# Task 03: sync codex drain wrapper with aeg/01's SKILL.md changes

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers. -->

Status: in-progress
Depends on: none
Priority: P2
Budget: 3 turns
Spec: ../SPEC.md (requirement R7 follow-up; convention: CLAUDE.md codex-leg bullet)
Touch: codex/.agents/skills/drain/SKILL.md

## Goal

The codex drain wrapper (a Codex-adapted paraphrase, 339 lines) reflects
the content aeg/01 and the 2026-07-11 SKILL.md changes added to
`.claude/skills/drain/SKILL.md`: the section-lookup pointer instruction
(content-equivalent of "load only the named section"), the gen-1
shell/run-naming step, and — only where the wrapper embeds worker-dispatch
guidance — content-equivalents of the "bare single command", "once per
edit round", and "under your worktree root" rules. Codex-adapt the
wording; anchors must appear literally so the greps below hold. CLAUDE.md's
codex-leg convention required this in aeg/01's Touch; this closes the gap.

## Steps

1. Read the wrapper; map which of the five items its structure embeds.
2. Add Codex-adapted lines carrying each literal anchor.

## Acceptance

- [ ] `grep -qi 'load only the named section' codex/.agents/skills/drain/SKILL.md && grep -qi 'bare single command' codex/.agents/skills/drain/SKILL.md && grep -qi 'once per edit round' codex/.agents/skills/drain/SKILL.md && grep -qi 'under your worktree root' codex/.agents/skills/drain/SKILL.md` → all hit
- [ ] MANUAL: run/tab-naming step present, Codex-adapted (Agent Manager naming surface or equivalent)
- [ ] `claude plugin validate .` → passes (codex/ is outside the plugin; guard against accidental plugin edits)
