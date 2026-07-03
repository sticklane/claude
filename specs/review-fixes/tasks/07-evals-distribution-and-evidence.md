# Task 07: Evals distribution caveat + conditional evidence commits

Status: pending
Depends on: 02, 05
Budget: 30 turns
Spec: ../SPEC.md (cluster 07)

## Goal

Two verified over-assumptions fixed: (a) /evals silently assumes the
toolkit repo layout (`evals/run.sh`, `.claude/skills/<skill>` fixtures)
but carries no caveat, unlike drain/design which say "works only in the
toolkit repo, not with installs"; (b) build's close-out commits a
verifier `evidence/` file unconditionally, and drain's DONE bullet +
tournament filter assert on that file — but the evidence path only exists
for `specs/<slug>/tasks/` layouts. Make the evidence contract conditional
and scoped. (Depends on task 02: both rewrite drain's DONE bullet and
reference — apply on top.)

## Touch

- `.claude/skills/evals/SKILL.md` and `.claude/skills/evals/reference.md`
  (distribution caveat)
- `.claude/skills/build/SKILL.md` (close-out evidence commit)
- `.claude/skills/drain/SKILL.md` (DONE bullet) and
  `.claude/skills/drain/reference.md` (tournament filter)
- `antigravity/.agents/workflows/build.md`,
  `antigravity/.agents/workflows/drain.md` (mirrors)

## Steps

1. Add the caveat to evals SKILL.md (near the top) and reference.md,
   matching drain's wording ("the toolkit repo, not with installs"):
   the runner and fixtures live in the toolkit repo; not usable from
   plugin installs.
2. In build's close-out, make the evidence commit conditional: "when an
   evidence path was passed; otherwise note non-persistence and put
   one-line evidence inline in the task file" (use that structure — the
   inline fallback must include the phrase "inline in the task file").
3. In drain's DONE bullet and the tournament filter in reference.md,
   scope the evidence-file assertions to queues using the
   `specs/<slug>/ layout` (use that phrase); for other layouts the
   inline evidence from step 2 is the artifact.
4. Mirror 2-3 into the antigravity build and drain workflows.

## Acceptance

- [ ] `grep -q "toolkit repo" .claude/skills/evals/SKILL.md && grep -qi "not usable from plugin installs\|not with installs" .claude/skills/evals/SKILL.md` → exit 0
- [ ] `grep -qi "not usable from plugin installs\|not with installs" .claude/skills/evals/reference.md` → exit 0
- [ ] `grep -q "inline in the task file" .claude/skills/build/SKILL.md` → exit 0 (conditional evidence with inline fallback)
- [ ] `grep -q "specs/<slug>/ layout" .claude/skills/drain/SKILL.md && grep -q "specs/<slug>/ layout" .claude/skills/drain/reference.md` → exit 0 (assertions scoped)
- [ ] `grep -q "inline in the task file" antigravity/.agents/workflows/build.md && grep -q "specs/<slug>/ layout" antigravity/.agents/workflows/drain.md` → exit 0 (mirrors)
