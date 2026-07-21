# ctx critical user journeys: the canonical query playbook

Breakdown-ready: true

## Problem

ctx has nine query commands and four in-flight improvement specs, but
no statement of the JOURNEYS they serve — so guidance (skill, CLAUDE.md
sections), acceptance framing, and gap analysis each re-derive "what is
this tool for" ad hoc. The 2026-07-20 fooszone survey (the first
sustained real-world exercise) plus the research base (Aider's
token-budgeted repo map; Codebase-Memory arXiv 2603.27277 — structure
index at ~10× fewer tokens / 2.1× fewer tool calls at 83% vs 92%
quality; Serena/LSP as precision layer) give enough evidence to fix
the journey set and let every other ctx spec anchor to it.

## Solution

One doctrine document, `docs/guides/ctx-cujs.md`, defining the eight
CUJs below — each with trigger, query sequence, expected token shape,
and known failure modes — plus a gap table mapping each CUJ to the
spec that serves it. The ctx skill and the ctx spec family then cite
CUJs by name instead of re-describing usage.

The eight CUJs (to be refined, not restated, in the doc):

1. ORIENT — "what is this codebase/module?" `map --limit` + `tree` per
   top dir. Failure modes: index pollution (minified/vendored —
   specs/ctx-minified-skip, specs/ctxignore-git-overlay), ranking
   noise (codebase-context-tree tasks/16).
2. LOCATE — "where is X / who calls X?" `refs`/`sig`, file-scoped
   selector on ambiguity (specs/ctx-query-ergonomics R1). Failure
   mode: heuristic misresolution (specs/ctx-static-analysis-
   augmentation F1).
3. DIG IN — "what's inside it?" `show` (specs/ctx-query-ergonomics
   R2); Read only past a symbol's span.
4. VERIFY ABSENCE — "is X gone?" `refs` no-match is NEVER sufficient;
   boundary-stating no-match output + suggested bounded content check
   (specs/ctx-absence-check). Live failure: figureBboxes 2026-07-20.
5. IMPACT — "what breaks if I change X?" `refs` (later `--exact` via
   LSP, augmentation F1) + `deps --reverse`.
6. SURVEY — "understand the repo deeply": batched recipe delegated to
   a cheap-tier scout (specs/ctx-skill-token-doctrine R4/R5).
7. DEDUP / DEAD CODE — "what's duplicated; what's only alive in dead
   zones?" zone-tagged refs (specs/ctx-dead-code-zones) + clone
   detection (augmentation F2). Dead-code FINDS are signal — Steven
   directive 2026-07-21: never blanket-exclude dead trees.
8. KNOWLEDGE — "what do we know about this symbol?" `notes` add/show;
   the durable-layer journey.

## Requirements

- R1 — `docs/guides/ctx-cujs.md` exists, ≤180 lines, one section per
  CUJ with the four fields (trigger, sequence, token shape, failure
  modes), each failure mode citing its owning spec by path. Acceptance:
  `grep -c '^## ' docs/guides/ctx-cujs.md` = 8; every
  `specs/ctx-*`/`specs/ctxignore-*` path cited resolves
  (`ls` each cited path).
- R2 — Gap table: the doc ends with a table mapping CUJ → serving
  spec(s) → status (shipped / specced / gap). Any cell marked "gap"
  must have a one-line proposed next step. Acceptance: table present;
  zero unexplained gaps.
- R3 — The ctx skill's body (`.claude/skills/ctx/SKILL.md` + the
  antigravity mirror, same-commit) links the doc once ("CUJ playbook:
  docs/guides/ctx-cujs.md") — this is a one-line addition and must
  respect the Landing order in specs/ctx-skill-token-doctrine (it
  lands last, after the ladder edits, to avoid the shared-surface
  merge trap).
- R4 — Each of the four in-flight ctx specs gains a one-line "Serves
  CUJ: <n>" annotation under its title (mechanical; no content
  change). Acceptance: `grep -l 'Serves CUJ' specs/ctx-*/SPEC.md`
  matches all four.

## Non-goals

- Changing any query behavior (the feature specs own that).
- A public/user-facing tutorial — this is agent doctrine.
