Status: draft
Discovered-from: specs/fleet-viz-css-resync/tasks/01-resync-and-drift-guard.md
Spec: ../SPEC.md
Blocking: no

# Protect fleet reference.md's viz-css block from the prettier format hook

The PostToolUse formatter (.claude/hooks/post-tool-format.sh) runs `prettier --write` on .md files, reformatting reference.md's embedded compact CSS into multi-line form on any Edit/Write-tool edit — silently breaking the byte-identity the drift guard (and shared-viz-renderer task 04) protects; a .prettierignore entry for the file (or the viz-css region) would harden the guarantee.

## Acceptance

<!-- draft: needs runnable criteria before promotion -->
