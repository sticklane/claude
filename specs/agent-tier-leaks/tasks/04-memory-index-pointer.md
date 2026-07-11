Status: draft
Discovered-from: specs/agent-tier-leaks/tasks/01-verifier-leak-trace.md
Spec: ../SPEC.md
Blocking: no
Promotion-ready: true
Promoted-by-run: 4e18a83a5654fba1
Depends on: none
Budget: 1 turn
Touch: docs/memory.md

# Task 04: Add docs/memory.md index pointer for verifier-tier-leak note

## Goal

Index the verifier-tier-leak memory note in `docs/memory.md` so it appears
in the load-on-demand lessons list, following the file's existing one-line
entry format.

## Acceptance

- [ ] `grep 'verifier-tier-leak' docs/memory.md` finds a one-line index
  entry matching the existing convention (lines 7–15):
  `- [verifier-tier-leak](memory/verifier-tier-leak.md) — <one-line hook>`
  — the hook description should be drawn from
  `docs/memory/verifier-tier-leak.md`'s own `Read when:` header, not
  invented.

## Original report

> docs/memory.md index pointer not added — task Steps §3 asks to add a
> pointer to `docs/memory.md`, but that file is outside this task's Touch
> ("verifier doc + memory note only"), so the new note lands un-indexed; a
> follow-up should add a one-line pointer in `docs/memory.md`.
