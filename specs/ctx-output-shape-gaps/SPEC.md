# ctx output shapes that push agents back to grep: silent empties and file-only listing

Serves CUJ: LOCATE, IMPACT (silent empties) and ORIENT (file listing) —
docs/guides/ctx-cujs.md.

Breakdown-ready: true

## Problem

Two output shapes observed in the 2026-07-21 cross-chat review
(../ctx-dispatch-adoption/evidence/ctx-usage-review-2026-07-21.md) made
the model abandon ctx mid-question and fall back to grep/find:

1. **Silent empty results.** Zero-result outcomes are indistinguishable
   from wrong queries. `ctx deps <path> --reverse` prints empty stdout
   with exit 0 BOTH for an indexed path with no importers AND for a
   typo'd/non-indexed path (live-verified 2026-07-21: `deps.rs` has no
   path-membership check — a nonexistent path and a real leaf return
   byte-identical emptiness). `ctx refs <symbol>` on a resolved symbol
   with zero references prints only its `def` line(s) with no ref lines
   and no explanation (the fooszone survey read this shape as "bare
   emptiness" and fell back to grep). In both cases the agent cannot
   distinguish "I queried the wrong thing" from "genuinely zero", so it
   re-asks with grep — the exact fallback ctx exists to avoid.
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
resolved-with-zero-results, the deps path-membership branch (absence-
check covers SYMBOL resolution only — `deps` takes a PATH, which no
sibling owns), and the listing mode. A symbol that fails to resolve
must keep emitting absence-check's boundary output, never R1's tail.

## Requirements

- R1 — Zero-result tails. Two commands, three branches, all tails on
  STDERR with exit code unchanged; `--json` output gains a `note` field
  (existing keys unchanged — the extend-never-replace contract
  absence-check R2 established):
  (a) `refs` with a resolved symbol and zero references: the `def`
  line(s) REMAIN on stdout exactly as today (suppressing them would
  regress the def-location answer); the stderr tail states "0
  references to <name>" using the QUERY argument, not a qpath — a
  resolved name may still carry multiple def rows across files, so a
  singular qpath would be ambiguous — and, when the symbol is a
  module/file-level symbol, suggests `ctx deps --reverse <its file>`
  for import-level callers.
  (b) `deps` (either direction) on an INDEXED path with zero edges:
  stdout stays empty; stderr tail states the fact, e.g. "no indexed
  importers of <path>" for `--reverse`.
  (c) `deps` on a path NOT in the index: stderr tail states
  "path not in index: <path>" — NEVER the zero-importers message.
  `deps` must therefore first check path membership; today a typo'd
  path and a real leaf return byte-identical emptiness, so an
  unconditional zero-importers tail would mechanize the absence
  fallacy this repo's specs exist to kill.
  Golden tests pin CLI and MCP surfaces for all three branches
  (including the (b)-vs-(c) distinction on a fixture with a known leaf
  and a nonexistent path), and pin that a filter-emptied result (once
  dead-code-zones lands) and a symbol no-match each do NOT emit R1's
  tail.

- R2 — `ctx tree --files <path>`: emit one indexed file path per line,
  no symbol lines; `--json` emits an array of paths. Composes with
  `--depth`, which in this mode means directory levels below `<path>`:
  files directly in `<path>` are depth 1, files one subdirectory down
  are depth 2, and so on — mirroring the existing "top-level is depth
  1" convention; depth is relative to the query path, never the index
  root. The count of emitted paths
  equals the index's file membership under the path — giving agents the
  file-list/count answer that awk+find approximated. Golden tests
  include a fixture directory where file count ≠ tree line count today.

- R3 — Docs rows (SKILL.md edit — registry slot required). The skill
  command table (+ antigravity mirror, same commit) gains the `--files`
  row and a one-line note that empty-vs-no-match outputs mean different
  things (pointing at the emitted tails). Registry mechanics — the
  breakdown session (not a dispatched worker) performs ALL of the
  following in one commit when it appends the slot to the SKILL.md
  editor registry in specs/ctx-skill-token-doctrine: (a) insert this
  spec's R3 slot immediately before the terminal ctx-cujs slot, which
  stays last; (b) increment the registry's opening "SEVEN specs" count
  to match the new total; (c) amend specs/ctx-cujs/tasks/02 to stay
  internally consistent: its landed-gate marker list gains this slot's
  marker, and EVERY count reference in that file increments — the
  "7-spec ... chain" length, the "SIX OTHER specs" enumerated list
  (adding this spec), the "ANY of the 6 markers" gate count, the
  "all 6 slots landed" echo, the frozen "SLOT 7" number, and the
  registry line citations — cujs task 02's gate greps exactly the
  predecessor markers, so without (c) "cujs lands last" is unenforced
  against this slot; check specs/ctx-cujs/DRAIN-OWNER.md for a live
  lease before amending (concurrent-sessions rule). R3's task lands serialized per
  the registry, after this spec's R1/R2 so the documented behavior
  exists. Acceptance: `grep -q '\-\-files' .claude/skills/ctx/SKILL.md`
  (confirmed absent today); mirror parity diff empty; plugin.json bump
  per conventions; the registry commit satisfies (a)–(c) in one diff.

## Non-goals

- No-match output (specs/ctx-absence-check) and filter tails
  (specs/ctx-dead-code-zones).
- Whole-tree text scanning at query time (architecture rule).
- `map` ranking or membership (tasks/16, ctxignore, minified-skip).

## Evidence

../ctx-dispatch-adoption/evidence/ctx-usage-review-2026-07-21.md
(fooszone F4/F6 instances; live repro commands 2026-07-21).

Next stage: /critique (this SPEC.md), then /breakdown.
