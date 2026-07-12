Status: pending
Discovered-from: specs/spec-completion-review/tasks/02-build-parity.md
Spec: ../SPEC.md
Blocking: no
Promotion-ready: true
Promoted-by-run: e83f34f07094a4fa
Depends on: 02-build-parity
Budget: 2 turns
Touch: antigravity/.agents/workflows/build.md, codex/.agents/skills/build/SKILL.md, .claude-plugin/plugin.json

# Task 05: Propagate the build spec-completion-review close-out into the antigravity + codex build ports

## Goal

The spec-completion-review close-out step now lives in the source build skill
(`.claude/skills/build/SKILL.md`) but is missing from its two downstream
ports, leaving gate-closed and codex installs on the older build close-out.
Carry that same step into `antigravity/.agents/workflows/build.md` and
`codex/.agents/skills/build/SKILL.md` (both real content, not symlinks), and
bump the plugin version to reflect the changed skill behavior. Match the
wording already used in the antigravity/codex drain ports for the equivalent
step so the two runtimes read consistently.

## Acceptance

- [ ] `grep -qi 'spec-completion review' antigravity/.agents/workflows/build.md`
  succeeds (currently 0 hits — the mirror gap this task closes).
- [ ] `grep -qi 'spec-completion review' codex/.agents/skills/build/SKILL.md`
  succeeds (currently 0 hits).
- [ ] `bash evals/lint-ultra-gate.sh` exits 0 (ultra-mention gate stays green;
  the source `.claude/skills/build/SKILL.md` is not edited here).
- [ ] `.claude-plugin/plugin.json` `version` is bumped from its pre-commit
  value within this task's own commit (`git show HEAD -- .claude-plugin/plugin.json`
  shows a `+` on the version line).
