# Codebase context tree (`ctx`)

## Problem

Agents burn context learning a repo's structure: whole-file reads to find
one signature, repeated scout dispatches to rediscover the same shape, and
no place to leave knowledge attached to a specific function that survives
refactorings. The toolkit's JIT-retrieval doctrine
(docs/guides/large-codebase-context.md) covers content search; nothing
covers structure. The research behind this spec — prior art, failed
approaches, and eleven maintainer-decided architecture forks — is in
docs/codebase-context-tree-research-2026-07.md (Verified: 2026-07-15);
this spec cites those decisions rather than re-arguing them.

## Solution

A new top-level component `context-tree/` (sibling of `agentprof/`,
`agent-console/`) shipping one CLI, working name `ctx`, plus an MCP wrapper
over the same core. tree-sitter parses each file in isolation into per-file
symbol facts (definitions, references, imports) mapped onto a small
universal symbol taxonomy — never a universal AST. A derived, ignored
SQLite index serves queries; agent notes live as version-tracked files
under `.context/notes/`. Sync is lazy (staleness sweep on every query),
change detection is VCS-agnostic with a git accelerator adapter, and every
query returns compact plain text sized to what was asked.

Implementation runtime: **Rust** (decided by /design, 2026-07-15). All 12
grammars ship as versioned crates.io releases — including tree-sitter-zig
1.1.2, tree-sitter-kotlin-ng 1.1.0, tree-sitter-ocaml 0.25.0, and
tree-sitter-haskell 0.23.1 — and the historical grammar-ABI lag is solved
(modern grammar crates depend on the version-agnostic
`tree-sitter-language` shim, so all 12 build against current core). The
exact architecture this spec needs — many grammars statically linked into
one CLI — is proven at 4× this scale by difftastic and ast-grep. Stack:
`tree-sitter` core + 12 grammar crates, `rusqlite` with the `bundled`
feature (no system SQLite), the official `rmcp` MCP SDK (stdio server),
`cargo test` + `insta` snapshots for golden-file verification, musl
targets for static release builds.

Architecture rules binding all requirements (rationale in the research
doc): per-file isolation at index time; index and query WORK is never
whole-tree — parsing is O(changed files) and query output is O(what was
asked) — while the staleness SCAN is O(tree) file stats in the no-VCS
baseline by construction and is delegated to VCS change feeds
(git fsmonitor in v1) at scale; layered node identity (qualified symbol
path + body content hash + tree-diff fallback); positions are snapshot
data, never identity; maintenance never calls a model.

## Contracts

Cross-cutting definitions the requirements reference. An implementer
invents nothing here.

- C1 — Qualified symbol path: components joined with `.`, as
  `<module>.<container>…<name>[#<n>]`. `<module>` is the language's own
  module/package concept where one exists (Python dotted module, Go
  package, Java/Kotlin package, Rust module path, OCaml module, Haskell
  module); where none does (C, C++ outside namespaces, Zig, Bash), it is
  the repo-relative file path with slashes replaced by `.` and the
  extension dropped. `<container>` is the chain of enclosing named symbols.
  `#<n>` is a 1-based source-order ordinal appended only when multiple
  definitions in the same module share the same path (e.g. C++ overloads);
  unique symbols carry no suffix. Paths are opaque strings to consumers.
- C2 — Body content hash: SHA-256 over the definition's full-span source
  bytes with the identifier-span bytes excised. A pure rename therefore
  leaves the hash unchanged; any signature or body edit changes it. (A
  body that embeds its own name — recursion — changes on rename and falls
  through to the tree-diff re-anchor path; that is expected.)
- C3 — Symbol argument resolution: commands taking `<symbol>` accept an
  exact qualified path (unique by C1) or a suffix of one. A suffix matching
  multiple symbols prints the candidate list (qualified path + file:line)
  and exits 3; `ctx notes add` refuses ambiguous anchors the same way.
- C4 — Project root and layout: the root is the nearest ancestor directory
  containing `.context/`, else the VCS adapter's root (`.git` in v1).
  `ctx init` scaffolds `.context/` containing `notes/` (version-tracked),
  `cache/` (derived index + journal, never committed), and a managed
  `.context/.gitignore` ignoring `cache/`. Every other command exits 2
  with a pointer to `ctx init` when no root is found.
- C5 — Sync journal: every sync appends one JSON line — UTC timestamp,
  trigger (`query` | `cli` | `hook`), files scanned/hashed/parsed — to
  `.context/cache/sync-journal.jsonl`. This is the synchronization point
  for observing background syncs.
- C6 — Store concurrency: SQLite in WAL mode with a busy timeout;
  concurrent syncs serialize on an advisory lock; queries read consistent
  snapshots and never block on a background sync.
- C7 — Token budget: token counts are ceil(bytes/4), documented as an
  approximation — deterministic, no tokenizer dependency.
- C8 — Docstrings: languages with a native convention use it (Python
  docstrings, Go doc comments, Rust `///`/`//!`, Javadoc, KDoc, Haddock,
  OCaml `(** *)`, JSDoc/TSDoc); languages without one (C, Zig, Bash) use
  the contiguous comment block immediately preceding the definition, if
  any. Absent both, the docstring fact is empty, not an error.
- C9 — Note provenance fields: `author` is `$CTX_AUTHOR`, else the VCS
  adapter's user identity, else `unknown`; `created` is ISO-8601 UTC.
  Snapshot tests normalize `id`, `created`, and `author`.

## Requirements

Extraction and index:

- R1: The extractor produces per-file symbol facts for Python,
  TypeScript/JavaScript (incl. TSX), Go, Rust, Java, C, C++, Zig, Kotlin,
  OCaml, Haskell, and Bash: every definition carries kind (small closed
  enum), name, qualified symbol path (C1), syntactic signature text,
  docstring (C8), full span and identifier span (line:col), parent
  containment, and body content hash (C2). Facts for a file derive from
  that file's content alone.
- R2: `ctx sync` updates the index incrementally: an mtime+size scan (or
  the VCS adapter's change feed) proposes candidates, content hashes
  confirm, and only genuinely changed files re-parse. Every sync appends a
  journal record (C5). `ctx sync --stats` reports files scanned, hashed,
  and parsed; after editing the content of exactly one file in a synced
  fixture, parsed == 1 and hashed == 1; a pure mtime bump with unchanged
  content yields parsed == 0.
- R3: Every query command runs the staleness sweep first (skippable with
  `--no-sync`), so query results always reflect the working tree.
- R4: The index respects ignore rules: the VCS adapter's ignores when
  present (`.gitignore` under git), plus `.ctxignore` in the no-VCS
  baseline; `.context/cache/` is never indexed.
- R5: The VCS adapter interface isolates change feeds, ignore rules,
  snapshot identity, user identity, and hook points. v1 ships the git
  adapter and the no-VCS baseline; the baseline path (root discovery per
  C4, ignores per R4) works in a plain directory that has never seen
  version control.

Queries (all: compact plain text by default, `--json` variant, never more
data than asked; `<symbol>` arguments resolve per C3):

- R6: `ctx tree <path> [--depth N]` prints the containment outline of the
  requested subtree only, honoring the depth cap.
- R7: `ctx sig <symbol>` prints the signature and first docstring line;
  `--doc` adds the full docstring.
- R8: `ctx map [--tokens N]` prints a ranked overview: symbols ordered by
  reference-graph importance, truncated to the token budget (default
  1000, counted per C7).
- R9: `ctx deps <path> [--reverse]` prints module-level import edges into
  or out of the requested path.
- R10: `ctx refs <symbol>` prints definitions and references, each result
  labeled `heuristic` (global-name match) or `precise` (LSP-resolved).
- R11: LSP enrichment is optional and additive: with a configured language
  server available, an enrichment pass stores resolved signatures and
  upgrades `ctx refs` results to `precise`; with none, every query still
  works from syntactic facts alone.

Notes:

- R12: `ctx notes add <symbol> <text> [--kind
gotcha|invariant|rationale|todo]` (body from the positional argument, or
  `--file <path>`, or stdin via `--file -`) writes one ULID-named markdown
  file under `.context/notes/` with YAML frontmatter: id, anchor qualified
  path (C1), anchor body hash (C2), optional kind, author and created
  (C9), status. `ctx notes <symbol>` prints that symbol's notes;
  `ctx notes list [--kind K] [--stale]` filters.
- R13: Re-anchoring is deterministic and layered: when an anchored symbol
  no longer resolves, sync re-anchors via qualified-name match, then
  body-hash match (C2), then tree-diff matching against the changed files'
  old and new trees; when the anchored body's hash changes, the note's
  status becomes stale with a pointer to what changed. Notes are never
  deleted or rewritten by the system; content revalidation is the reading
  agent's job.
- R14: Notes merge under plain VCS semantics: one file per note, so
  concurrent edits to the same note surface as an ordinary merge conflict
  and nothing else conflicts.

Surface and integration:

- R15: An MCP server exposes the same query and note verbs as typed tools,
  as a thin wrapper over the CLI core (no second implementation of query
  logic).
- R16: `ctx hooks install` installs opt-in pre-warm hooks: VCS hooks
  (git's post-checkout/post-merge/post-commit in v1) and a printed snippet
  for a harness PostToolUse hook, each running `ctx sync` in the
  background (journaled per C5). Hook files are managed as delimited
  blocks: install appends a marked `ctx` block to an existing hook file
  (creating an executable file only if absent), preserving all existing
  content; `ctx hooks uninstall` removes exactly that block and deletes
  only files `ctx` itself created.
- R17: A README in `context-tree/` documents install, `ctx init`, the
  query surface, the note format, and the documented check command that
  runs the component's full test suite.
- R18: `ctx init` scaffolds the `.context/` layout per C4 and is
  idempotent (re-running on an initialized root changes nothing and exits
  0).

## Out of scope

- Semantic/vector search (route to claude-context per
  docs/guides/large-codebase-context.md).
- Sub-symbol (span-in-symbol) note anchors — whole-symbol only in v1.
- VCS adapters beyond git (interface only; Sapling/EdenFS, Perforce are
  future adapters).
- Automatic note rewriting by a model — staleness is flagged, never
  auto-repaired.
- Cross-repo indexing, code editing/refactoring commands, call graphs
  beyond def/ref, and any change to `.claude/rules/token-discipline.md`
  scout routing (post-v1 doctrine question).
- Sharded multi-database storage — v1 is one SQLite file; the schema keys
  per-file facts so sharding by subtree is possible later without
  redesign, but no shard implementation ships in v1.
- Sub-file incremental re-parse (tree-sitter edit deltas) — the v1 rework
  unit is the file.

## Acceptance criteria

Anchoring note: `context-tree/`, `specs/codebase-context-tree/tasks/`, and
`.context/` do not exist in the repo today (verified 2026-07-15), so none
of these pass vacuously. Commands assume the component's documented check
command from R17; fixture layout is the implementer's choice under
`context-tree/tests/fixtures/` except where a criterion pins it.

- [ ] `context-tree/` exists with a build producing a `ctx` executable;
      `ctx --version` exits 0 and prints a version (covers R17 scaffold;
      target dir absent today, verified 2026-07-15).
- [ ] Language coverage is mechanically enumerable, independent of the
      suite passing: `context-tree/tests/fixtures/languages/` contains
      exactly 12 subdirectories named python, typescript, go, rust, java,
      c, cpp, zig, kotlin, ocaml, haskell, bash, each holding at least one
      source file, and the R1 golden tests iterate over that directory
      listing (not a hardcoded subset).
- [ ] The documented check command (R17) runs the component's test suite
      green, covering R1 (per-language extraction golden tests incl. a C++
      overload fixture exercising C1's `#<n>` rule and a C2 test proving a
      pure rename leaves the body hash unchanged), R4 (ignored file
      excluded from index), R5 (index builds in a fixture directory with
      no `.git`), R6–R10 (query output golden tests incl. depth cap, C7
      token budget, C3 ambiguous-suffix exit code 3, and
      `heuristic`/`precise` labels), R12 (note file format, C9 fields
      normalized in snapshots), R14 (two divergent copies of one note file
      produce a VCS conflict, nothing else), and R18 (init idempotence).
- [ ] Incrementality (R2/R3): e2e test syncs a fixture, edits the content
      of one file, and asserts `ctx sync --stats` reports parsed == 1 and
      hashed == 1; a pure mtime bump yields parsed == 0; a query without
      `--no-sync` reflects the edit.
- [ ] Re-anchoring (R13), all three layers: (a) rename a function in-file
      → note re-anchors via body hash, status fresh; (b) edit the function
      body → status stale, pointer present; (c) move a function to a
      different file, rename it, AND make a small body edit in the same
      sync → note re-anchors via tree-diff to the new symbol and status is
      stale. In all cases the note file is never deleted.
- [ ] LSP enrichment (R11): with a language server configured in the test
      environment, `ctx refs` on a fixture symbol returns at least one
      `precise` result; with none, the same query returns `heuristic`
      results and exits 0. If no language server is installable in the
      unattended test environment, the worker marks this criterion
      manual-pending with the reason stated
      (docs/memory/unattended-worker-tool-limits.md) rather than skipping
      silently.
- [ ] MCP (R15): a scripted MCP client lists the tools and round-trips one
      `ctx tree`-equivalent call against a fixture.
- [ ] Hooks (R16): in a throwaway git fixture whose post-checkout hook
      already contains non-ctx content, `ctx hooks install` preserves that
      content and appends the marked block; a checkout then produces a
      `trigger: hook` record in the sync journal (C5) within a bounded
      poll (≤10s); `ctx hooks uninstall` restores the original hook bytes
      exactly.
- [ ] End-to-end as a user would: script drives `ctx init` → `ctx map` →
      `ctx sig` → `ctx notes add` → refactor → stale flag →
      `ctx notes list --stale`, on a fixture repo containing at least 3 of
      the 12 languages.

## Open questions

None.

## Appendix: rejected options (runtime decision, /design 2026-07-15)

- Go: runner-up. Official Go bindings exist for 11/12 grammars but
  tree-sitter-zig ships none (hand-maintained cgo shim required), and
  every future language addition replays that bindings roulette; cgo is
  mandatory either way, so agentprof/'s pure-Go precedent was unreachable
  regardless. Flip scenario: maintainer weighs single-toolchain repo
  uniformity above grammar-ecosystem fit.
- Python: ruled out by the maintainer before investigation — the
  100k-file/100M-headroom scale posture sits poorly on interpreter startup
  for a sync-on-every-query CLI.
- Investigator evidence (binding coverage, ABI status, SDK maturity, with
  source URLs) is recorded in this branch's /design run; the research doc
  carries the surviving citations.
