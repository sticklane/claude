# Task 02: closing gate — antigravity port line + plugin bump

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers. -->

Status: in-progress
Depends on: 01
Priority: P2
Budget: 3 turns
Spec: ../SPEC.md (requirement R3)
Touch: antigravity/.agents/workflows/drain.md, .claude-plugin/plugin.json

## Goal

The antigravity drain workflow carries a content-equivalent block titled
exactly "Hub-economics advisory" (body may paraphrase for the Antigravity
runtime — the runtime discloses models differently, so its text may say
"where the runtime discloses the session model"); the plugin version is
bumped in THIS task's own commit; `claude plugin validate .` passes.

## Steps

1. Add the paraphrased block near the port's startup/naming area, title
   literal.
2. Bump `.claude-plugin/plugin.json` version RELATIVE to the value read
   at your own base (never a pinned literal — the agent-efficiency-guards
   closing task bumps the same line; whichever lands second rebases and
   still bumps cleanly).
3. `claude plugin validate .`.

## Acceptance

- [ ] `grep -qi 'hub-economics advisory' antigravity/.agents/workflows/drain.md` → hits
- [ ] `claude plugin validate .` → passes
- [ ] This task's own commit modifies the version line:
  `git show HEAD -- .claude-plugin/plugin.json | grep -q '^+.*"version"'`
  run immediately after the closing commit lands (immune to sibling-spec
  bumps earlier in the run)
