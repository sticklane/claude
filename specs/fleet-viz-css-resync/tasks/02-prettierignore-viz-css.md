# Task 02: Protect fleet reference.md's viz-css block from the prettier format hook

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers. -->

Status: pending
Depends on: none
Priority: P2
Budget: 6 turns
Spec: ../SPEC.md
Discovered-from: specs/fleet-viz-css-resync/tasks/01-resync-and-drift-guard.md
Touch: .prettierignore

## Goal

The PostToolUse formatter (`.claude/hooks/post-tool-format.sh` running
`prettier --write` on `.md` files) reformats `fleet/reference.md`'s
embedded compact CSS into multi-line form on any Edit/Write-tool edit —
silently breaking the byte-identity the drift guard
(`tests/test_fleet_css_drift.sh`) protects. A `.prettierignore` entry for
the file hardens the guarantee so future agents can edit it with normal
tools.

## Steps

1. Prove the hazard first: run prettier --write on a scratch copy of
   `.claude/skills/fleet/reference.md` and confirm the drift test goes
   red against it.
2. Add `.claude/skills/fleet/reference.md` to `.prettierignore` (create
   at repo root if absent).
3. Re-run: prettier --write on the real file is now a no-op and the
   drift test stays green.

## Acceptance

- [ ] `grep -q "\.claude/skills/fleet/reference\.md" .prettierignore` → match
- [ ] `npx --yes prettier --write .claude/skills/fleet/reference.md && bash tests/test_fleet_css_drift.sh` → exit 0 (use the repo's installed prettier if npx is unavailable)
- [ ] `git diff --stat -- .claude/skills/fleet/reference.md` → empty after the prettier run above
