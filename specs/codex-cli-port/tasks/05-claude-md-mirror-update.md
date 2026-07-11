# Task 05: CLAUDE.md three-way mirror-convention update

Status: in-progress
Depends on: 01, 02, 03
Priority: P2
Budget: 20 turns
Spec: ../SPEC.md (requirements R6; Solution item 3)
Touch: CLAUDE.md

## Goal

CLAUDE.md's mirror-convention bullet (currently the paragraph beginning
"`.claude/` is the source of truth; `antigravity/` is a mirrored port...",
around lines 78-85) is rewritten to describe the three-way `.claude/` →
`antigravity/` → `codex/` relationship (real copies → real copies →
symlinks-plus-four-real-skills), and extends the `Touch:`-discipline
sentence to cover the four codex skill wrappers and the symlink-maintenance
obligation from the spec's Solution item 3.

## Touch

Only `CLAUDE.md`. This task does not touch anything under `codex/` or
`antigravity/` — it only documents the structure tasks 01-03 already built.

## Steps

1. Locate the current bullet in `/Users/sjaconette/claude/CLAUDE.md`:

   > - `.claude/` is the source of truth; `antigravity/` is a mirrored port
   >   (skills near-identical, agents→skills, human-only skills→workflows,
   >   hooks in Antigravity's JSON shape). When a skill changes here, mirror
   >   the change there in the same commit. A spec whose tasks change
   >   `.claude/skills/` files must carry the mirror + plugin.json bump in
   >   some task's `Touch:` (typically one closing task) — drained workers
   >   can't touch unlisted paths, so an unlisted mirror silently ships
   >   un-mirrored (bit queue 5's shared-viz spec; workboard-cli's closing
   >   task 04 is the model).

2. Rewrite it to add the `codex/` leg: `.claude/` → `antigravity/` (full
   mirrored port, real copies) → `codex/` (thin overlay: symlinks the ~15
   already-working `antigravity/.agents/skills/*` directories plus
   `_shared`, adds only the four explicit-invocation-only skill wrappers —
   `drain`/`build`/`autopilot`/`evals` — as real content). Extend the
   `Touch:`-discipline sentence: a task whose `Touch:` changes one of the
   four `.claude/skills/{drain,build,autopilot,evals}/SKILL.md` files must
   also carry the matching `codex/.agents/skills/<name>/SKILL.md` update in
   its `Touch:`; a task that renames or removes any already-working
   `antigravity/.agents/skills/*` directory must also update the matching
   symlink under `codex/.agents/skills/`, since a dangling symlink silently
   drops that skill from Codex's discovery root.
3. Re-run the R4 diff check against the final repo state to confirm nothing
   drifted across tasks 01-03 (see Acceptance below — note the
   `antigravity/.agents/skills/drain` non-skill script-bundle entry from
   task 01's landmine note is excluded from both sides of the comparison,
   since it was never symlinked).
4. Commit.

## Acceptance

- [ ] `grep -q "codex/" CLAUDE.md` and the mirror-convention paragraph
  mentions all three of `.claude/`, `antigravity/`, and `codex/`
- [ ] `diff <(ls antigravity/.agents/skills | grep -v -E '^drain$') <(ls codex/.agents/skills | grep -v -E '^(drain|build|autopilot|evals)$')` produces no output
- [ ] `find codex/.agents/skills -maxdepth 1 -type l | wc -l` → `16`
