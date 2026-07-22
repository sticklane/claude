---
name: ctx
description: Answers code-structure questions from the context-tree index (the repo's `ctx` CLI) instead of reading whole files — symbol trees, signatures, cross-file references, import graphs, enclosing-symbol lookup at file:line, and durable symbol-anchored notes that survive refactors. Use for "where is X defined", "what calls X / references X", "what's the signature of X", "what does this file import / depend on", "map the codebase", "what's at <file>:<line>", or to leave/read a note on a symbol ("add a note on this function", "any gotchas recorded here?"). Also trigger on tool-directive phrasing ("use ctx", "with ctx"/"via ctx", "the ctx skill", "ctx the codebase") and survey-shaped requests ("understand the codebase", "survey the repo structure", "deep-dive the code structure"). Not for content/text search (grep/Grep fits that) and not worth bootstrapping for a one-off question in an unindexed repo.
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

## Reading ladder

Escalate in order — stop at the cheapest rung that answers the question, and
never jump straight to a whole-file Read:

1. **ctx query** — any structural question (where/what-shape/who-calls/
   imports/encloses). Returns lines, not files.
2. **Structural content search** — for body/literal/pattern questions ctx
   can't answer: `ast-grep` where available (structural, syntax-aware), else
   `Grep` capped with `-l` (names only) or `-C 0` (no context lines).
3. **Sliced Read** — when a specific body must actually be read, Read with
   `offset`/`limit` around a ctx-reported line (`ctx at <file>:<line>` or a
   `refs`/`sig` line gives you the number), not the whole file.
4. **Whole-file Read** — only when you are about to edit the file.

Escalate off rung 1 on exactly these triggers:

- **Symbol not indexed** — ctx returns nothing and the extractor doesn't
  cover that language (rung 2).
- **Identical-qpath ambiguity** — two defs share a qualified path so ctx
  can't disambiguate; confirm the right one by reading its body (rung 3).
- **`heuristic` tag on a load-bearing ref** — a ref ctx flags `heuristic`
  (best-effort, not resolved) that a decision depends on: verify it (rung 2/3).
- **Body/literal/pattern questions** — "what string does it return", "which
  branch sets X" — content ctx doesn't carry (rung 2).

## Output hygiene

ctx output is for a decision, not for the transcript — keep it bounded:

- **Cap wide output.** Pipe `map`/`tree`/`refs` through `head`, or slice with
  `--limit` / `--json | jq`. Worked example:
  `ctx map --limit 30 | head` (top refs only);
  `ctx refs Foo --json | jq -r '.[].file'` (just the files).
- **Batch independent queries** into one shell invocation
  (`ctx sig Foo; ctx refs Foo; ctx deps bar.py`) rather than one round-trip
  each.
- **Paste only what the decision needs.** Never dump a full `tree`/`refs`
  into conversation when the answer is one symbol or one count — summarize
  the rest.

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
  tools (`claude mcp add ctx -- /abs/path/to/ctx mcp`); useful when a
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
