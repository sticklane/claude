# CUJ-6 — Portability read

Live, 2026-07-22. From a bare shell — no plugin, no skills, jq only —
answer "what is in progress" from the committed JSONL export:

## Scratch repo

```
jq -r 'select(.status != "closed") | "\(.id)\t\(.status)\t\(.title)"' \
  .beads/issues.jsonl
cuj1-ifj  open  parser chokes on unicode widget names
cuj1-3sm  open  seed: first epic — wire the widget pipeline
```

## This repo

The same query against the committed `.beads/issues.jsonl` returns the
live queue (epic `agentic-5ge` and its open children) with no bd
binary involved; `bd list --json` gives the richer view when bd IS
installed. This is the data-level portability the 2026-07-22 pivot
promises: any agent that can read a file can read the queue.
`.agents/skills/beads/SKILL.md` (committed by the curated init) is the
generic-agent onboarding for the same layer.
