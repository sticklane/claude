# ctx output shapes that push agents back to grep: silent empties and file-only listing

Serves CUJ: LOCATE, IMPACT (silent empties) and ORIENT (file listing) —
docs/guides/ctx-cujs.md.

Breakdown-ready: true

## Problem

Two output shapes observed in the 2026-07-21 cross-chat review
(../ctx-dispatch-adoption/evidence/ctx-usage-review-2026-07-21.md) made
the model abandon ctx mid-question and fall back to grep/find:

1. **Silent empty results.** A query that RESOLVES but has zero results
   prints nothing and exits 0: `ctx refs possessionAnalyzer` (a module
   symbol with no symbol-level refs) and `ctx deps <file> --reverse`
   (no indexed importers) both returned bare emptiness in the fooszone
   survey; live-reproduced 2026-07-21 (`ctx deps --reverse <file>` →
   empty stdout, exit 0). The agent cannot distinguish "I queried the
   wrong thing" from "genuinely zero", so it re-asks with grep — the
   exact fallback ctx exists to avoid.
2. **No files-only listing.** "Which files are under tests/?" has no ctx
   answer shape: `tree` always interleaves symbols under each file
   header (`--depth 1` caps symbol nesting but still emits symbol
   lines — live-verified), so the survey session piped `ctx tree tests |
   awk '/^tests/'` twice and still cross-checked with `find` because
   tree line counts ≠ file counts.

Seams (one sentence each, mirroring the sibling convention):
specs/ctx-absence-check owns resolution FAILURE ("no symbol matches" —
boundary note + suggested grep); specs/ctx-dead-code-zones owns
results emptied by filters (its filter tail); THIS spec owns
resolved-with-zero-results and the listing mode. A symbol that fails to
resolve must keep emitting absence-check's boundary output, never R1's
tail.

## Requirements

- R1 — Zero-result tails. `refs` with a resolved symbol and zero
  references, and `deps` (either direction) with zero edges, append a
  one-line diagnostic tail to STDERR stating what was searched and the
  most likely next query: refs-on-a-module-symbol suggests `ctx deps
  --reverse <its file>`; empty `deps --reverse` states "no indexed
  importers of <path>". stdout stays empty; exit code unchanged;
  `--json` output gains a `note` field (existing keys unchanged — the
  extend-never-replace contract absence-check R2 established). Golden
  tests pin CLI and MCP surfaces, and pin that a filter-emptied result
  (once dead-code-zones lands) and a no-match each do NOT emit R1's
  tail.

- R2 — `ctx tree --files <path>`: emit one indexed file path per line,
  no symbol lines; `--json` emits an array of paths. Composes with
  `--depth` (directory depth in this mode). The count of emitted paths
  equals the index's file membership under the path — giving agents the
  file-list/count answer that awk+find approximated. Golden tests
  include a fixture directory where file count ≠ tree line count today.

- R3 — Docs rows (SKILL.md edit — registry slot required). The skill
  command table (+ antigravity mirror, same commit) gains the `--files`
  row and a one-line note that empty-vs-no-match outputs mean different
  things (pointing at the emitted tails). Breakdown of this spec must
  first append a slot for R3 to the SKILL.md editor registry in
  specs/ctx-skill-token-doctrine, inserted before the terminal
  ctx-cujs R3 slot (which stays last); R3 lands serialized per that
  registry, after this spec's R1/R2 so the documented behavior exists.
  Acceptance: `grep -q '\-\-files' .claude/skills/ctx/SKILL.md`
  (confirmed absent today); mirror parity diff empty; plugin.json bump
  per conventions.

## Non-goals

- No-match output (specs/ctx-absence-check) and filter tails
  (specs/ctx-dead-code-zones).
- Whole-tree text scanning at query time (architecture rule).
- `map` ranking or membership (tasks/16, ctxignore, minified-skip).

## Evidence

../ctx-dispatch-adoption/evidence/ctx-usage-review-2026-07-21.md
(fooszone F4/F6 instances; live repro commands 2026-07-21).

Next stage: /critique (this SPEC.md), then /breakdown.
