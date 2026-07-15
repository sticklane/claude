# Task 05: Retire codex's autopilot skill, fold into build/SKILL.md, sweep doctrine mentions

Status: in-progress
Depends on: 01
Priority: P1
Budget: 6 turns
Spec: ../SPEC.md (requirements R7a, R6 codex portion)
Touch: codex/.agents/skills/autopilot/, codex/.agents/skills/build/SKILL.md, codex/AGENTS.md, codex/README.md, codex/.agents/skills/drain/SKILL.md, codex/.agents/skills/evals/SKILL.md

## Goal

`codex/.agents/skills/autopilot/` no longer exists; its content is folded
into `codex/.agents/skills/build/SKILL.md` (codex has no `reference.md`
pattern — everything folds into the one SKILL.md file). Every codex file
naming autopilot as one of "the four" launch-gated/real-content codex
skills now names the three-skill set (drain/build/evals).

## Touch

Exactly the files listed above. Do not touch `.claude/` or `antigravity/`
(other tasks own those trees).

## Steps

1. Read `codex/.agents/skills/autopilot/` in full (confirmed real content
   per CLAUDE.md's codex port-chain convention: `SKILL.md`, ~110 lines,
   plus `agents/openai.yaml`; not a symlink).
2. Fold its content into `codex/.agents/skills/build/SKILL.md` (codex has
   no separate reference-file pattern; everything lands in the one
   SKILL.md). This is the same file the codex-doctrine "four"→"three"
   fixes below also touch, so make both edits in one pass to avoid a
   second read-modify-write on the same file.
3. Delete `codex/.agents/skills/autopilot/`.
4. `codex/AGENTS.md`, `codex/README.md` (multiple mentions — re-verify
   current locations with `grep -n autopilot codex/README.md`, the spec's
   own line numbers are a snapshot, not a contract), `codex/.agents/skills/drain/SKILL.md`,
   and `codex/.agents/skills/evals/SKILL.md` all name autopilot as one of
   "the four" launch-gated/real-content codex skills — each becomes the
   three-skill set (drain/build/evals).

## Acceptance

- [ ] `[ ! -d codex/.agents/skills/autopilot ]`
- [ ] `codex/.agents/skills/build/SKILL.md` contains the folded-in content
      from the deleted autopilot skill.
- [ ] `! grep -q 'autopilot' codex/AGENTS.md codex/README.md codex/.agents/skills/drain/SKILL.md codex/.agents/skills/evals/SKILL.md`
- [ ] Each of the four files above names the three-skill set
      (drain/build/evals) wherever it previously named "the four" —
      spot-check by reading the surrounding context after the grep above.
