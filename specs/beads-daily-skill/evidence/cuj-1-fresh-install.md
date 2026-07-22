# CUJ-1 — Fresh install

Two live runs, 2026-07-22.

## Scratch repo (clean-room)

```
mktemp -d; git init cuj1; BD_NON_INTERACTIVE=1 bd init -q .
bd create "seed: first epic — wire the widget pipeline" -t epic -p 1
bd ready
  ○ cuj1-3sm ● P1 [epic] seed: first epic — wire the widget pipeline
  Ready: 1 issues with no active blockers
```

Empty-queue repo → init → seed → `bd ready` answers on day one.

## This repo (the real install, curated per the spec)

- `bd init` ran; its auto-commit was reshaped (commit `9def8d6`):
  interactions.jsonl untracked, CLAUDE.md block scoped, `Bash(bd *)`
  allowlist added, auto-export on, `.beads/issues.jsonl` committed.
- `bin/install-gates .` wired the bd-compliance Stop hook (commit
  `2376d48`): settings Stop array carries
  `.claude/hooks/bd-compliance.sh`.
- `/work` is registered: the harness skill listing shows it with its
  trigger phrases ("what's next", "work the queue", "track this").

Pending (needs a session that starts fresh): observing "what's next"
auto-trigger `/work` in a brand-new session. Registration and trigger
phrases are in place; the live-trigger observation is MANUAL-PENDING.
