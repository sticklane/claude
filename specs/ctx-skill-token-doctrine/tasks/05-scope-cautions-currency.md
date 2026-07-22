# Task 05: Scope cautions currency (R7)

Status: done
Depends on: 04
Priority: P3
Budget: 8 turns
Spec: ../SPEC.md (requirement R7)
Touch: .claude/skills/ctx/SKILL.md, antigravity/.agents/skills/ctx/SKILL.md

## Goal

The ctx skill's scope cautions are current and complete. Add four cautions:
(1) refs/sig results are name-resolution heuristics (tagged `heuristic`), not
compiler-verified — point to specs/ctx-static-analysis-augmentation for the
exactness path; (2) identical-qpath collisions across directories are
unresolvable via `sig` (fall back to sliced Read); (3) `map` noise from
committed vendored/generated trees is an index-membership problem fixed by
specs/ctxignore-git-overlay, not by more querying; (4) the ABSENCE FALLACY —
"no symbol matches" means no _symbol_ by that name, never that the string is
absent from code (object fields, JSON keys, string literals are not indexed),
so an absence claim must be grep-verified before asserting it. Mirror all four
into the antigravity ctx SKILL.md.

## Touch

Scope-cautions area of `.claude/skills/ctx/SKILL.md` and its antigravity
mirror. This is the last ctx SKILL.md edit in this spec's serial chain
(after task 04). Later specs (ctx-minified-skip, ctx-dead-code-zones,
ctx-absence-check) rewrite these R7 cautions, so keep them an identifiable,
self-contained block.

## Steps

1. Read the current "Scope cautions" text in ctx SKILL.md.
2. Add the four cautions above, keeping cross-references to
   specs/ctx-static-analysis-augmentation and specs/ctxignore-git-overlay.
3. Port the four cautions into `antigravity/.agents/skills/ctx/SKILL.md`.
4. Run the acceptance commands.

## Acceptance

- [x] `grep -qi 'heuristic' .claude/skills/ctx/SKILL.md && grep -qi 'not compiler-verified\|exactness\|ctx-static-analysis' .claude/skills/ctx/SKILL.md` → exit 0 (caution 1)
- [x] `grep -qi 'qpath\|identical' .claude/skills/ctx/SKILL.md && grep -qi 'sliced read\|fall back' .claude/skills/ctx/SKILL.md` → exit 0 (caution 2)
- [x] `grep -qi 'ctxignore-git-overlay\|vendored\|index-membership' .claude/skills/ctx/SKILL.md` → exit 0 (caution 3)
- [x] `grep -qi 'ABSENCE FALLACY' .claude/skills/ctx/SKILL.md && grep -qi 'grep-verified\|string literal\|json key' .claude/skills/ctx/SKILL.md` → exit 0 (caution 4)
- [x] `grep -qi 'ABSENCE\|heuristic' antigravity/.agents/skills/ctx/SKILL.md && grep -qi 'ctxignore\|vendored' antigravity/.agents/skills/ctx/SKILL.md` → exit 0 (mirror coverage)
