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
   the working tree (span from the index, bytes from the file — stays
   consistent with lazy staleness sweep). `--head N` truncates long
   bodies; default prints whole span with a truncation guard (e.g. cap
   at 200 lines with a "… +K more lines, use --head/Read" tail).
3. `--in <path-prefix>` (repeatable) and `--not-in <path-prefix>` on
   `refs` (and `map`), filtering results by file path prefix.

## Requirements

- R1 — Selector: `sig`/`refs`/`show`/`notes` accept `<path>:<name>`;
  for the two-`main.rodSpecs` fixture shape, the file-scoped form
  returns exactly one result and the bare form's ambiguity listing
  includes the rerun hints. Golden tests (insta) for both.
- R2 — `ctx show`: output is exactly the symbol's span (verified
  against a fixture with known line ranges); respects staleness (edit
  the fixture, query again, get new bytes); truncation guard behavior
  pinned; `--json` returns `{path, start_line, end_line, text}`.
- R3 — Filters: `refs <sym> --in go/cmd --not-in attic` returns only
  matching paths; filters compose with the existing output format and
  `--json`. Golden tests.
- R4 — Docs: skill command table (both `.claude/skills/ctx/SKILL.md`
  and the antigravity mirror) gains rows for `show` and the selector/
  filter forms; the reading ladder in specs/ctx-skill-token-doctrine R2
  is updated so rung 3 becomes `ctx show` (sliced Read demotes to rung
  4's about-to-edit case).
- R5 — Architecture rules hold: no whole-tree work at query time; the
  span lookup is O(one symbol), the file read is O(one file).

## Non-goals

- Cross-file body concatenation or multi-symbol dumps (invites token
  blowouts; one symbol per `show`).
- Ranking changes to `map` (specs/codebase-context-tree tasks/16).
- Exactness/LSP (specs/ctx-static-analysis-augmentation).
