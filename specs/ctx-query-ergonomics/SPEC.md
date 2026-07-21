# ctx query ergonomics: file-scoped selectors, symbol-bounded body retrieval, ref filters

Breakdown-ready: true

## Problem

A full ctx-driven codebase survey (fooszone, 2026-07-20 — the first
sustained real-world exercise of the query surface) surfaced three
ergonomic gaps in the CLI itself, distinct from index membership
(specs/ctxignore-git-overlay) and from precision
(specs/ctx-static-analysis-augmentation):

1. **Identical-qpath collisions are a dead end.** `ctx sig main.rodSpecs`
   is permanently ambiguous when `go/cmd/mlhybrid/main.go` and
   `attic/go-cmd/mloverlay/main.go` both define `main.rodSpecs` — the
   qualified path (SPEC C1) has no file component, and `sig` offers no
   way to pick one. The session fell back to `sed`.
2. **No symbol-bounded content retrieval.** After locating a def, the
   next question is often "what's in the body?" (is it hardcoded? what
   does the switch do?). ctx knows the symbol's exact line span but
   offers nothing between `sig` (header only) and a raw file Read; the
   session used `sed -n 1678,1700p` with a guessed range. A
   symbol-bounded dump is the token-shaped answer: exactly the body,
   no more.
3. **No query-time path filter.** `refs lerp` returns attic/ hits
   interleaved with live code. Even once .ctxignore membership lands,
   transient narrowing ("refs, but only under go/cmd/") requires
   grep-postprocessing of output.

## Solution

Three additive query features, no index-schema change (all data —
file path, symbol line span — is already in the index):

1. File-scoped selector accepted wherever a symbol is accepted:
   `<path>:<name>` (e.g. `go/cmd/mlhybrid/main.go:rodSpecs`), and a
   `--in <path-prefix>` flag as the disambiguating filter form.
   Ambiguity listings (already emitted) gain a "rerun with" hint line
   showing the file-scoped form for each candidate.
2. `ctx show <symbol> [--head N]`: print the symbol's source span from
   the working tree. `show` MUST run the lazy staleness sweep before
   resolving the span (like every other query) — the span is then read
   from the freshly-reconciled index, so an edit that shifts the
   symbol's lines cannot produce a stale-range dump. `--head N`
   truncates long bodies; default prints whole span with a truncation
   guard (e.g. cap at 200 lines with a "… +K more lines, use
   --head/Read" tail).
3. `--in <path-prefix>` (repeatable) and `--not-in <path-prefix>` on
   `refs` (and `map`), filtering results by file path prefix.

## Requirements

- R1 — Selector: `sig`/`refs`/`show`/`notes` accept `<path>:<name>`;
  for the two-`main.rodSpecs` fixture shape, the file-scoped form
  returns exactly one result and the bare form's ambiguity listing
  includes the rerun hints. Golden tests (insta) for both.
- R2 — `ctx show`: output is exactly the symbol's span (verified
  against a fixture with known line ranges); staleness test MUST use a
  span-shifting edit — insert/delete lines ABOVE the symbol so its line
  range moves, query again, and assert the returned span is
  re-resolved to the new location (a fixed-range re-read would fail
  this); truncation guard behavior pinned; `--json` returns
  `{path, start_line, end_line, text}`.
- R3 — Filters: `refs <sym> --in go/cmd --not-in attic` returns only
  matching paths; filters compose with the existing output format and
  `--json`. Golden tests.
- R4 — Docs: skill command table (both `.claude/skills/ctx/SKILL.md`
  and the antigravity mirror) gains rows for `show` and the selector/
  filter forms; the reading ladder (created by
  specs/ctx-skill-token-doctrine R2) is rewritten to exactly this
  four-rung list, verbatim: (1) ctx query; (2) structural content
  search (ast-grep where available, else Grep) for body/literal/pattern
  questions; (3) `ctx show <symbol>` when a located symbol's body must
  be read; (4) Read — sliced (`offset`/`limit`) when needed context
  exceeds one symbol's span, whole-file only when about to edit. This
  supersedes token-doctrine's original rung 3 ("sliced Read"); both
  specs agree on this final list. Landing order: this task lands AFTER
  ctx-skill-token-doctrine R2 and after any
  ctx-static-analysis-augmentation SKILL.md edits, serialized, editing
  skill + mirror in the same commit.
- R5 — Architecture rules hold: no whole-tree work at query time; the
  span lookup is O(one symbol), the file read is O(one file).

## Non-goals

- Cross-file body concatenation or multi-symbol dumps (invites token
  blowouts; one symbol per `show`).
- Ranking changes to `map` (specs/codebase-context-tree tasks/16).
- Exactness/LSP (specs/ctx-static-analysis-augmentation).
