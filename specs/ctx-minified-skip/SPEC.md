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

At index time, before parsing, classify each CANDIDATE file — defined
as a file one of the `context-tree/src/lang/` extractors would accept;
files no extractor parses (.md, .json, .css, sourcemaps) are not
candidates and are untouched by this spec. Classified-minified
candidates are recorded in the index as skipped-with-reason (so tree
can show them) and produce no symbols. Detection stays heuristic and
conservative — the cost of a false positive (a real source file
skipped) is silent blindness, so thresholds favor false negatives and
every skip is visible.

Detection signal (tunable constants, pinned by tests):

- Name pattern: `*.min.js`, `*.min.mjs` (extractor-covered extensions
  only — there is no CSS extractor, so `.min.css` is out of scope) —
  always skipped.
- Content heuristics for unsuffixed bundles, requiring file > 50 KB
  AND either: (a) average line length > 400 bytes; or (b) total line
  count ≤ 5 AND the largest line holds > 50% of file bytes (the
  whole-bundle-on-one-line shape). The ≤ 5-line guard deliberately
  exempts a normal source file containing one giant embedded literal
  (base64 blob amid ordinary code) — that class must NOT be skipped,
  and R3 pins it with a fixture. Sourcemap comments
  (`//# sourceMappingURL=`) may strengthen but never suffice alone.

Escape hatch (decided — the `.ctxignore` grammar is subtractive-only
per ctxignore-git-overlay R2 and the shipped `CtxignoreOverlay`, so
`!` negation is NOT available): a new optional sibling file
`.ctxkeep`, same glob grammar as `.ctxignore` (reuse the existing
matcher), whose sole semantic is "exempt matching paths from minified
auto-skip". It is NOT a general re-include and cannot override
`.ctxignore` membership.

## Requirements

- R1 — Classification runs per-candidate-file at index time (per-file
  isolation preserved; O(changed files)); result stored with a reason
  enum (`minified-name` / `minified-content`). Re-classification
  follows the same staleness rules as parsing.
- R2 — Skipped files yield zero symbols in `map`/`refs`/`sig`;
  `ctx tree <dir>` lists them with a `(skipped: minified)` marker —
  a NEW file-level output class: today tree renders only
  symbol-bearing files, and non-candidate files (.md, .json) remain
  omitted as before; only minified-skipped CANDIDATES gain the listed
  marker (a skip must never look like absence, but non-parseable
  files were never expected present). Acceptance: golden tests with a
  committed `*.min.js` fixture and a generated ≤5-line single-line
  bundle fixture: `map` output contains none of their symbols; `tree`
  shows both with the marker; a `.md` file in the same fixture dir
  stays unlisted.
- R3 — False-positive guards, three fixtures, none skipped: (a) a
  normal source file > 50 KB with ordinary line lengths; (b) a source
  file with many ordinary lines plus one embedded > 50%-of-bytes
  literal line (the ≤ 5-line guard's reason to exist); (c) a
  `.ctxkeep`-matched copy of the minified fixture (escape hatch
  works). Plus one golden asserting `.ctxkeep` does NOT resurrect a
  `.ctxignore`-excluded path.
- R4 — Docs: context-tree docs + the ctx skill scope cautions replace
  the vendored-noise caution (authored by
  specs/ctx-skill-token-doctrine R7 — HARD DEPENDENCY: this task
  cannot land before R7 has) with the two-mechanism story (minified
  auto-skip vs explicit .ctxignore membership vs .ctxkeep exemption).
  This holds SLOT 4 of the SKILL.md editor registry in
  token-doctrine's Landing order; skill + antigravity mirror
  same-commit.

## Non-goals

- General vendored-code exclusion (membership —
  specs/ctxignore-git-overlay).
- Non-candidate file types (.min.css, sourcemaps, JSON data,
  lockfiles) — no extractor parses them, so there is nothing to skip;
  they gain no markers.
- Beautified-bundle detection (normal line lengths, generated
  content) — undetectable cheaply; membership config owns it.
- Any model/LLM involvement (maintenance never calls a model).
