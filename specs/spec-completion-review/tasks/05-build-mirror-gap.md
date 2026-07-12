Status: draft
Discovered-from: specs/spec-completion-review/tasks/02-build-parity.md
Spec: ../SPEC.md
Blocking: no

# Mirror the build SKILL.md spec-completion-review sentence into the antigravity + codex build ports

Task 02 added the spec-completion-review close-out sentence to
`.claude/skills/build/SKILL.md`, but the spec's closing task 03 mirrors only
the DRAIN files (its Touch = antigravity/.agents/workflows/drain.md,
codex/.agents/skills/drain/SKILL.md, .claude-plugin/plugin.json). The build
change therefore ships un-mirrored to `antigravity/.agents/workflows/build.md`
and `codex/.agents/skills/build/SKILL.md` (both real content, currently 0-hit
on the "spec-completion review" anchor), violating CLAUDE.md's port-chain
convention. Gate-closed / codex installs will read the old build close-out
without the spec-completion-review step. Needs the two mirror edits plus a
plugin.json bump — a human should amend scr/03's Touch or add a task, since
drain cannot edit a task's read-only Touch.

## Acceptance

<!-- draft: needs runnable criteria before promotion -->
