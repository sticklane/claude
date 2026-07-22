# Task 05: Docs + ctx skill scope cautions (two-mechanism story)

Status: blocked
Unblock: run: d=specs/ctx-skill-token-doctrine/tasks; if [ ! -d "$d" ]; then echo "not done: ctx-skill-token-doctrine not broken down"; else for f in "$d"/*.md; do grep -q '^Status: done' "$f" || echo "not done: $f"; done; fi
Depends on: 01, 02, 03, 04
Priority: P3
Budget: 14 turns
Spec: ../SPEC.md (requirement R4)
Touch: context-tree/README.md, .claude/skills/ctx/SKILL.md, antigravity/.agents/skills/ctx/SKILL.md, .claude-plugin/plugin.json

## Goal

The context-tree docs and the ctx skill scope cautions replace the
vendored-noise caution (authored by specs/ctx-skill-token-doctrine R7) with
the two-mechanism story: minified auto-skip (zero-config, mechanical) vs
explicit `.ctxignore` membership vs `.ctxkeep` exemption. The ctx skill edit
and its antigravity mirror land in the same commit; `plugin.json` version is
bumped because skill behavior changed.

## Touch

HARD CROSS-SPEC DEPENDENCY: this task rewrites text that
specs/ctx-skill-token-doctrine R7 authors ("vendored-noise caution"). It
holds SLOT 4 of that spec's SKILL.md editor registry Landing order and MUST
land AFTER R7. Nothing auto-flips this blocked status: `/drain` does not
re-run `Unblock: run:` on a pre-existing blocked task, so a human or later
session must re-check that ctx-skill-token-doctrine's tasks are all `done`
(and specifically that R7's scope-caution text has landed in
`.claude/skills/ctx/SKILL.md`) before flipping Status to `pending`. Edit the
`.claude` skill and its `antigravity` mirror in the same commit
(prose ports are paraphrased, not byte-identical — write matching content,
never a `diff`-clean copy).

## Steps

1. Confirm the blocker cleared: R7's vendored-noise scope caution is present
   in `.claude/skills/ctx/SKILL.md`. If absent, stop — do not author over a
   caution that has not landed.
2. In `.claude/skills/ctx/SKILL.md`, replace the vendored-noise caution with
   the two-mechanism story (minified auto-skip vs `.ctxignore` membership vs
   `.ctxkeep` exemption). Mirror the same content into
   `antigravity/.agents/skills/ctx/SKILL.md` (paraphrased port).
3. Update `context-tree/README.md` scope/behavior docs to describe minified
   auto-skip, the `minified-name`/`minified-content` reasons, the tree
   `(skipped: minified)` marker, and the `.ctxkeep` exemption.
4. Bump `version` in `.claude-plugin/plugin.json` (skill behavior changed).

## Acceptance

- [ ] `grep -q 'ctxkeep' .claude/skills/ctx/SKILL.md && grep -qi 'minified' .claude/skills/ctx/SKILL.md` → both present (two-mechanism story landed).
- [ ] `grep -q 'ctxkeep' antigravity/.agents/skills/ctx/SKILL.md && grep -qi 'minified' antigravity/.agents/skills/ctx/SKILL.md` → mirror carries the same concepts.
- [ ] `grep -qi 'minified' context-tree/README.md` → README documents the behavior.
- [ ] `test "$(git show HEAD~:.claude-plugin/plugin.json | grep '\"version\"')" != "$(grep '\"version\"' .claude-plugin/plugin.json)"` → plugin version changed from this task's base commit (compare against base, never a pinned literal).
- [ ] Manual-pending: live antigravity mirror cross-reference sweep (closure-triggered, per .claude/rules/mirror-verification.md) — an unattended worker marks this manual-pending with the reason "antigravity live check requires interactive runtime"; a human or orchestrator runs it post-merge.
