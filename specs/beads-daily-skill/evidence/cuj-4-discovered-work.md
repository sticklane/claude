# CUJ-4 — Discovered work

Two live runs, 2026-07-22.

## Scratch repo

```
bd create "parser chokes on unicode widget names" -t bug -p 1 \
  --deps discovered-from:cuj1-90m                → cuj1-ifj
bd show cuj1-ifj
  DISCOVERED FROM
    ◊ ✓ cuj1-90m: implement the widget parser ● P1
```

## This repo (dogfood — a real bug, not a fixture)

Mid-task, running `bin/install-gates .` on this repo surfaced a real
bug: bd sets `core.hooksPath=.beads/hooks`, and the installer archived
bd's own pre-commit as a "foreign hook". It was filed before fixing:

```
bd create "install-gates archives bd's own pre-commit when
  core.hooksPath=.beads/hooks" -t bug -p 1 \
  --deps discovered-from:agentic-rp6             → agentic-1bx
```

then claimed, fixed red-green (`tests/test_install_gates.sh`,
176/176), and closed with the reason recorded — the provenance edge
links the bug to the task that surfaced it (commit `2376d48`).
