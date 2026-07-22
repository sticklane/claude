# Task 07: Plugin version bump + mirror closure sweep

Status: in-progress
Depends on: 01, 03, 04, 05, 06
Priority: P3
Budget: 6 turns
Spec: ../SPEC.md (closing task — plugin distribution + mirror verification)
Touch: .claude-plugin/plugin.json

## Goal

The distributed plugin reflects the changed skill behavior and the mirrors
are verified as landed. The ctx and onboard skills changed behavior (trigger
surface, new body sections, onboard procedure), so `.claude-plugin/plugin.json`
`version` is bumped once for this spec's release. This closing task also runs
the closure-triggered cross-reference sweep over the touched antigravity
mirrors (per `.claude/rules/mirror-verification.md`) — confirming the ctx,
scout, and onboard mirrors carry the ported content and their cross-references
resolve under antigravity.

## Touch

`.claude-plugin/plugin.json` only (the single `version` field). The mirrors
themselves are edited inline by tasks 01–06; this task does not re-edit them,
it verifies them. It runs last because it depends on every skill-editing task
having landed.

## Steps

1. Read the current `version` in `.claude-plugin/plugin.json` and bump it
   (patch bump is sufficient for skill-behavior changes).
2. Verify the antigravity mirrors for ctx, scout, and onboard carry the
   ported content (content-coverage) and that any cross-references they name
   resolve under the antigravity tree.
3. Run the acceptance commands.

## Acceptance

- [ ] `test "$(git show HEAD:.claude-plugin/plugin.json | sed -n 's/.*"version": *"\([^"]*\)".*/\1/p')" != "$(sed -n 's/.*"version": *"\([^"]*\)".*/\1/p' .claude-plugin/plugin.json)"` → exit 0 (version changed from this task's base-commit value, not a hard-coded literal)
- [ ] `grep -qi 'ladder\|survey\|ABSENCE' antigravity/.agents/skills/ctx/SKILL.md` → exit 0 (ctx mirror carries R2/R4/R7 content)
- [ ] `grep -qi 'ctx' antigravity/.agents/skills/scout/SKILL.md` → exit 0 (scout mirror carries prefer-ctx guidance)
- [ ] `grep -qi 'structure question\|ctx\|index-first' antigravity/.agents/skills/onboard/SKILL.md` → exit 0 (onboard mirror carries R6 content)
