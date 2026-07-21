---
name: ctx
description: Answers code-structure questions from the context-tree index (the repo's `ctx` CLI) instead of reading whole files — symbol trees, signatures, cross-file references, import graphs, enclosing-symbol lookup at file:line, and durable symbol-anchored notes that survive refactors. Use for "where is X defined", "what calls X / references X", "what's the signature of X", "what does this file import / depend on", "map the codebase", "what's at <file>:<line>", or to leave/read a note on a symbol ("add a note on this function", "any gotchas recorded here?"). Not for content/text search (grep/Grep fits that) and not worth bootstrapping for a one-off question in an unindexed repo.
---

# ctx — query the code-structure index

Resolve the binary, in order: `ctx` on PATH → `context-tree/target/release/ctx`
(this repo) → build once with `cargo build --release` in `context-tree/`
(requires Rust; ~1–2 min). One-time per repo: `ctx init` at the repo root.
There is NO manual sync step — every query lazily sweeps staleness first, so
results reflect the working tree as of the query.

Prefer a ctx query over reading a file whenever the question is structural
(where/what-shape/who-calls) — it returns lines, not files, which is exactly
the token-discipline delegation default (cite `.claude/rules/token-discipline.md`).
Fall back to Grep for content/text questions, and to reading the file only
when you are about to edit it.

## Query commands

| Question                               | Command                   |
| -------------------------------------- | ------------------------- |
| What's in this dir/file, structurally? | `ctx tree <path>`         |
| Signature + doc of a symbol?           | `ctx sig <name-or-qpath>` |
| Most-referenced symbols overall?       | `ctx map [--limit N]`     |
| What does this file import?            | `ctx deps <file>`         |
| Who references this symbol?            | `ctx refs <name>`         |
| What encloses this line?               | `ctx at <file>:<line>`    |

All take `--json` for structured output. Symbols accept short names or
qualified paths (`pkg.mod.Class.method`); ambiguous short names list their
candidates. `refs` output tags each def with `[notes:N]` when notes are
anchored there — follow up with `ctx notes <symbol>`.

## Notes — durable, refactor-surviving knowledge

- `ctx notes add <symbol> "<text>" --kind gotcha|invariant|rationale|todo`
- `ctx notes <symbol>` (show) · `ctx notes list [--file <path>]`

Notes are version-tracked files under `.context/notes/`, anchored to the
symbol (not the line): edits and moves re-anchor them, and staleness is
flagged rather than silently lost. Leave a note when you learn something
about a function the code cannot say itself (the same bar as a code
comment, but surviving across sessions). The index DB itself is derived
and gitignored; only notes are committed.

## Optional wiring

- `ctx hooks install` — git pre-warm hooks + a managed pre-commit that
  keeps note anchors written; prints a PostToolUse snippet that surfaces a
  file's notes to the agent at edit time.
- `ctx mcp` — stdio MCP server exposing the same nine queries as typed
  tools (register the stdio command `ctx mcp` in this harness's MCP config); useful when a
  harness prefers tools over shell.
- `.ctxignore` at the repo root — a subtractive exclusion overlay honored
  in both VCS and no-VCS modes, for dropping committed-but-derived paths
  (checked-in `dist/`, vendored code, generated artifacts) the VCS itself
  can't ignore.

Scope cautions: extractors cover python, go, js, ts, bash, c, cpp, zig,
kotlin, java, ocaml, haskell — NOT rust; `map` ranking currently
over-weights bash locals on mixed repos (spec stub 16). Capability
evidence: `specs/codebase-context-tree/evidence/capability-shakedown-2026-07-20.md`.

Next stage: none — tool-usage skill; queries and notes land in the working
tree (notes committed by whoever owns the current change).
