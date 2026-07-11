# Task 02: closing gate — antigravity port lines + plugin bump

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers. -->

Status: in-progress
Depends on: 01
Priority: P2
Budget: 3 turns
Spec: ../SPEC.md (requirement R7)
Touch: antigravity/.agents/workflows/drain.md, .claude-plugin/plugin.json

## Goal

The antigravity drain workflow port carries content-equivalent lines for
R1 (Bash-denial stop), R3 (re-read discipline), and R4 (worktree-root
edit rule), each containing its literal anchor phrase ("bare single
command", "once per edit round", "under your worktree root" — body text
may otherwise paraphrase for the Antigravity runtime). The plugin version
is bumped in THIS task's own commit, RELATIVE to the value read at this
task's base (never a pinned literal — specs/drain-hub-economics's closing
task bumps the same line; whichever lands second rebases and still bumps
cleanly). `claude plugin validate .` passes.

## Steps

1. Add the three anchored lines to the port's worker-dispatch area.
2. Read current plugin version, bump patch, commit.
3. `claude plugin validate .`.

## Acceptance

- [ ] `grep -qi 'bare single command' antigravity/.agents/workflows/drain.md && grep -qi 'once per edit round' antigravity/.agents/workflows/drain.md && grep -qi 'under your worktree root' antigravity/.agents/workflows/drain.md` → all hit (R7)
- [ ] `claude plugin validate .` → passes
- [ ] This task's own commit modifies the version line:
  `git show HEAD -- .claude-plugin/plugin.json | grep -q '^+.*"version"'`
  run immediately after the closing commit lands
