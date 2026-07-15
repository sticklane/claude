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
doc): per-file isolation at index time; no whole-tree enumeration on any
path (100k files v1, 100M headroom); layered node identity (qualified
symbol path + body content hash + tree-diff fallback); positions are
snapshot data, never identity; maintenance never calls a model.

## Requirements

Extraction and index:

- R1: The extractor produces per-file symbol facts for Python,
  TypeScript/JavaScript (incl. TSX), Go, Rust, Java, C, C++, Zig, Kotlin,
  OCaml, Haskell, and Bash: every definition carries kind (small closed
  enum), name, qualified symbol path, syntactic signature text, docstring
  (per the language's convention: Python docstrings, Go doc comments, Rust
  `///`, Javadoc, etc.), full span and identifier span (line:col), parent
  containment, and body content hash. Facts for a file derive from that
  file's content alone.
- R2: `ctx sync` updates the index incrementally: an mtime+size scan (or
  the VCS adapter's change feed) proposes candidates, content hashes
  confirm, and only genuinely changed files re-parse. `ctx sync --stats`
  reports files scanned, hashed, and parsed; after touching exactly one
  file in a synced fixture, parsed == 1.
- R3: Every query command runs the staleness sweep first (skippable with
  `--no-sync`), so query results always reflect the working tree.
- R4: The index respects ignore rules: the VCS adapter's ignores when
  present (`.gitignore` under git), plus `.ctxignore` in the no-VCS
  baseline.
- R5: The VCS adapter interface isolates change feeds, ignore rules,
  snapshot identity, and hook points. v1 ships the git adapter and the
  no-VCS baseline; the baseline path works in a plain directory that has
  never seen version control.

Queries (all: compact plain text by default, `--json` variant, never more
data than asked):

- R6: `ctx tree <path> [--depth N]` prints the containment outline of the
  requested subtree only, honoring the depth cap.
- R7: `ctx sig <symbol>` prints the signature and first docstring line;
  `--doc` adds the full docstring.
- R8: `ctx map [--tokens N]` prints a ranked overview: symbols ordered by
  reference-graph importance, truncated to the token budget (default
  1000).
- R9: `ctx deps <path> [--reverse]` prints module-level import edges into
  or out of the requested path.
- R10: `ctx refs <symbol>` prints definitions and references, each result
  labeled `heuristic` (global-name match) or `precise` (LSP-resolved).
- R11: LSP enrichment is optional and additive: with a configured language
  server available, an enrichment pass stores resolved signatures and
  upgrades `ctx refs` results to `precise`; with none, every query still
  works from syntactic facts alone.

Notes:

- R12: `ctx notes add <symbol> [--kind gotcha|invariant|rationale|todo]`
  writes one ULID-named markdown file under `.context/notes/` with YAML
  frontmatter (id, anchor symbol path, anchor body hash, optional kind,
  author, created, status); `ctx notes <symbol>` prints that symbol's
  notes; `ctx notes list [--kind K] [--stale]` filters.
- R13: Re-anchoring is deterministic: when an anchored symbol is renamed or
  moved, sync re-anchors the note via qualified-name match, then body-hash
  match, then tree-diff matching; when the anchored body's hash changes,
  the note's status becomes stale with a pointer to what changed. Notes are
  never deleted or rewritten by the system; content revalidation is the
  reading agent's job.
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
  background. `ctx hooks uninstall` reverses it.
- R17: A README in `context-tree/` documents install, the query surface,
  the note format, and the documented check command that runs the
  component's full test suite.

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

## Acceptance criteria

Anchoring note: `context-tree/`, `specs/codebase-context-tree/tasks/`, and
`.context/` do not exist in the repo today (verified 2026-07-15), so none
of these pass vacuously. Commands assume the component's documented check
command from R17; fixture repo layout is the implementer's choice under
`context-tree/` test data.

- [ ] `context-tree/` exists with a build producing a `ctx` executable;
      `ctx --version` exits 0 and prints a version (covers R17 scaffold;
      target dir absent today, verified 2026-07-15).
- [ ] The documented check command (R17) runs the component's test suite
      green, covering R1 (per-language extraction golden tests across all
      12 languages), R4 (ignored file excluded from index), R5 (index
      builds in a fixture directory with no `.git`), R6–R10 (query output
      golden tests incl. depth cap, token budget, and
      `heuristic`/`precise` labels), R12 (note file format), and R14 (two
      divergent copies of one note file produce a VCS conflict, nothing
      else).
- [ ] Incrementality (R2/R3): e2e test syncs a fixture, touches one file,
      and asserts `ctx sync --stats` reports parsed == 1; a query without
      `--no-sync` reflects the edit.
- [ ] Re-anchoring (R13): e2e test adds a note to a function, renames the
      function in-file (note re-anchors, status fresh), then edits the
      function body (status becomes stale, pointer present), and asserts
      the note file was never deleted.
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
- [ ] Hooks (R16): in a throwaway git fixture, `ctx hooks install` then a
      checkout triggers a background sync (observable via `--stats` or a
      sync journal); `ctx hooks uninstall` removes the hooks.
- [ ] End-to-end as a user would: script drives init → `ctx map` →
      `ctx sig` → note add → refactor → stale flag → `ctx notes list
--stale`, on a fixture repo containing at least 3 of the 12
      languages.

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
