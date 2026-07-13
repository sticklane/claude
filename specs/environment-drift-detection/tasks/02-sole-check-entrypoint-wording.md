# Task 02: state scripts/check.sh as the sole required check entrypoint

Status: pending
Depends on: none
Priority: P2
Budget: 12 turns
Spec: ../SPEC.md (requirement R2)
Touch: .claude/skills/build/SKILL.md, .claude/skills/drain/SKILL.md, .claude/skills/drain/reference.md, antigravity/.agents/workflows/build.md, antigravity/.agents/workflows/drain.md, codex/.agents/skills/build/SKILL.md, codex/.agents/skills/drain/SKILL.md, .claude-plugin/plugin.json

## Goal

`.claude/skills/build/SKILL.md`'s verify step and `.claude/skills/drain/
SKILL.md`'s merge-then-gate step (plus `.claude/skills/drain/reference.md`'s
"project gates" language, e.g. its line "Then **merge → run project gates →
delete...") each state explicitly, in prose, that `scripts/check.sh` is the
sole required check entrypoint for both a dispatched worker's own
verification and drain's own merge-time gate run — never a hand-derived
list of steps read out of CLAUDE.md prose. The change lands identically in
this repo's mirrors: `antigravity/.agents/workflows/build.md`,
`antigravity/.agents/workflows/drain.md`, `codex/.agents/skills/build/
SKILL.md`, and `codex/.agents/skills/drain/SKILL.md`.

## Touch

This task edits wording only — no procedural steps change, no new sections.
Do not touch `bin/install-gates` or `templates/check.sh.tmpl` (Task 01 owns
those). Do not touch any other skill's SKILL.md. `antigravity/.agents/
skills/build/` and `antigravity/.agents/skills/drain/` do NOT exist as
skill directories (verified during critique) — antigravity mirrors both
`build` and `drain` as workflows only (`.agents/workflows/{build,drain}.md`,
per CLAUDE.md's "human-only skills→workflows" mirror rule); do not create
new files under `antigravity/.agents/skills/`. `codex/.agents/skills/
{build,drain}/SKILL.md` are real files (not symlinks to antigravity) —
each needs its own matching edit.

## Steps

1. Read `.claude/skills/build/SKILL.md`'s verify step (its "verify the
   working tree against the acceptance criteria" section) and add a
   sentence stating `scripts/check.sh` is the sole required check
   entrypoint — never a hand-derived list of steps read out of CLAUDE.md
   prose.
2. Read `.claude/skills/drain/SKILL.md`'s merge-then-gate line ("Then
   **merge → run project gates → delete...**") and add the same
   sole-entrypoint statement there. Then read `.claude/skills/drain/
reference.md`'s "project gates" occurrences (its Status-table row for
   `done`, its post-merge description, and its "project gates pass" line)
   and add the sole-entrypoint statement to at least one of them too —
   R2 names `reference.md`'s "project gates" language explicitly as part
   of what must change, not just `SKILL.md`.
3. Port the identical wording into `antigravity/.agents/workflows/build.md`
   and `antigravity/.agents/workflows/drain.md` at their equivalent verify/
   merge-gate points (per `.claude/rules/mirror-procedure-discipline.md`:
   same content, not a rewrite). Surrounding sentence structure may adapt
   to the workflow's own voice, but the literal phrase `sole required
check entrypoint` must appear verbatim in both mirrors — this task's
   own acceptance criteria grep for that exact string, so a paraphrase of
   the phrase itself (not just its surrounding prose) fails acceptance.
4. Port the identical wording into `codex/.agents/skills/build/SKILL.md`
   and `codex/.agents/skills/drain/SKILL.md` at their equivalent points.
5. `drain` and `build` are two of the four ultra-path skills — run
   `bash evals/lint-ultra-gate.sh` and confirm it exits 0 (it checks every
   case-insensitive "ultra" mention stays within +/-3 lines of the literal
   "active runtime profile" marker in these files; a wording edit near an
   "ultra" mention can violate this — reposition rather than removing the
   marker if it does).
6. Per CLAUDE.md's authoring conventions ("Bump `version` in `plugin.json`
   whenever skill behavior changes"): bump the `version` field in
   `.claude-plugin/plugin.json` (a patch-level bump is sufficient for a
   wording-only change).
7. Run this repo's own check command before committing.

## Acceptance

- [ ] `grep -c "sole required check entrypoint" .claude/skills/build/SKILL.md` → greater than 0
- [ ] `grep -c "sole required check entrypoint" .claude/skills/drain/SKILL.md` → greater than 0
- [ ] `grep -c "sole required check entrypoint" .claude/skills/drain/reference.md` → greater than 0
- [ ] `grep -c "sole required check entrypoint" antigravity/.agents/workflows/build.md` → greater than 0
- [ ] `grep -c "sole required check entrypoint" antigravity/.agents/workflows/drain.md` → greater than 0
- [ ] `grep -c "sole required check entrypoint" codex/.agents/skills/build/SKILL.md` → greater than 0
- [ ] `grep -c "sole required check entrypoint" codex/.agents/skills/drain/SKILL.md` → greater than 0
- [ ] `bash evals/lint-ultra-gate.sh` → exits 0
- [ ] the `version` field in `.claude-plugin/plugin.json` differs from its
      value at this task's own base commit (compare via
      `git show <base-commit>:.claude-plugin/plugin.json | grep version`,
      never a hard-coded pre-task literal, per breakdown's version-bump
      acceptance convention)
