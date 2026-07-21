# ctx: detect minified/generated-bundle content and skip parsing it

Serves CUJ: ORIENT (docs/guides/ctx-cujs.md, via specs/ctx-cujs).

Breakdown-ready: true

## Problem

Steven directive (2026-07-21): minified JS "is a problem and we
shouldn't be processing" it — as an INDEXER capability, not a
membership config. Live evidence: fooszone's root `paper-full.min.js`
made `ctx map` ~90% noise (hundreds of one-letter symbols like
`paper-full.min.t#1`…), burying every real symbol; the ORIENT CUJ was
unusable in exactly the repo that most needed it. `.ctxignore`
(specs/ctxignore-git-overlay) requires someone to notice and configure;
minified content is mechanically detectable and should be skipped by
default with zero config.

## Solution

At index time, before parsing, classify each candidate file with a
cheap content check; classified-minified files are recorded in the
index as skipped-with-reason (so tree/map can show them) but produce
no symbols. Detection stays heuristic and conservative — the cost of a
false positive (a real source file skipped) is silent blindness, so
thresholds favor false negatives and every skip is visible.

Detection signal (tunable constants, pinned by tests):

- Name pattern: `*.min.js`, `*.min.css`, `*.min.mjs` — always skipped.
- Content heuristics for unsuffixed bundles, ALL required to trigger:
  file > 50 KB; AND (average line length > 400 bytes OR a single line
  > 5000 bytes holds > 50% of file bytes). Sourcemap comment
  > (`//# sourceMappingURL=`) may strengthen but never suffices alone.

## Requirements

- R1 — Classification runs per-file at index time (per-file isolation
  preserved; O(changed files)); result stored with a reason enum
  (`minified-name` / `minified-content`). Re-classification follows
  the same staleness rules as parsing.
- R2 — Skipped files yield zero symbols in `map`/`refs`/`sig`;
  `ctx tree <dir>` lists them with a `(skipped: minified)` marker
  rather than omitting them (visibility rule — a skip must never look
  like absence). Acceptance: golden test with a committed minified
  fixture (name-pattern) and a generated single-line fixture
  (content-pattern): map/refs contain none of their symbols; tree
  shows both with the marker.
- R3 — False-positive guard: golden test that a normal long source
  file (> 50 KB, ordinary line lengths — generate a fixture) is NOT
  skipped; and a one-line escape hatch documented (re-include via
  `.ctxignore`-family config or a `!` override — reuse the existing
  matcher grammar, do not invent new syntax; coordinate with
  specs/ctxignore-git-overlay so overlay-excluded and
  minified-skipped reasons stay distinct in output).
- R4 — `ctx map` on a fixture repo containing the minified fixture
  ranks only real symbols. Acceptance: golden map output contains no
  fixture-bundle symbols.
- R5 — Docs: context-tree docs + the ctx skill scope cautions replace
  "map noise from committed vendored trees is a membership problem"
  with the two-mechanism story (minified auto-skip vs explicit
  .ctxignore membership) — skill+mirror same-commit, respecting the
  Landing order in specs/ctx-skill-token-doctrine.

## Non-goals

- General vendored-code exclusion (that is membership —
  specs/ctxignore-git-overlay).
- Beautified-bundle detection (normal line lengths, generated content)
  — undetectable cheaply; membership config owns it.
- Any model/LLM involvement (maintenance never calls a model).
