# Codebase context tree (`ctx`)

Breakdown-ready: true

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
targets for static release builds. Grammar crates are optional Cargo
dependencies behind a default-on feature flag (ast-grep's proven
packaging shape), keeping the 12 statically linked by default while
allowing trimmed builds.

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
  exact qualified path (unique by C1) or a suffix of one on `.`-delimited
  component boundaries — the argument must equal one or more whole
  trailing components (`Handler` matches `app.Handler`, not
  `app.AuthHandler`). A suffix matching multiple symbols prints the
  candidate list (qualified path + file:line) and exits 3; `ctx notes add`
  refuses ambiguous anchors the same way. A symbol argument matching
  nothing exits 1 with a not-found message.
- C4 — Project root and layout: the root is the nearest ancestor directory
  containing `.context/`. Only `ctx init` falls back to the VCS adapter's
  root (`.git` in v1) — to decide where to scaffold. `ctx init` creates
  `.context/` containing `notes/` (version-tracked), `cache/` (derived
  index + journal, never committed), and a managed `.context/.gitignore`
  ignoring `cache/`. `cache/` carries a schema version; a
  version-mismatched or corrupt cache is rebuilt transparently from
  source (derived state), never a user-facing error. Every other command exits 2 with a pointer to
  `ctx init` whenever no ancestor `.context/` exists — even inside a VCS
  repo.
- C5 — Sync journal: every sync appends one JSON line — UTC timestamp,
  trigger (`query` | `cli` | `hook`), files scanned/hashed/parsed, and
  `pending_reanchors` (count of anchor updates computed but not yet
  written at a persistence point, R13 phase 2) — to
  `.context/cache/sync-journal.jsonl`. This is the synchronization point
  for observing background syncs.
- C6 — Store concurrency: SQLite in WAL mode with a busy timeout;
  concurrent syncs serialize on an advisory lock; queries read consistent
  snapshots and never block on a background sync. A query whose staleness
  sweep finds the sync lock already held skips its own sweep and reads the
  current snapshot (the in-flight sync publishes the update); it never
  blocks and never runs a second concurrent sweep.
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
- C10 — Note-presence markers: every query output line that names a
  symbol carrying notes appends `[notes:<count>]`, with a trailing `!`
  (`[notes:2!]`) when any of them is stale. This is the push channel that
  makes notes discoverable without asking; the index already joins
  symbol→note for derived freshness, so the marker costs one lookup and
  ~5 output tokens. Markers are ordinary output bytes and count toward
  any C7 budget.

## Requirements

Extraction and index:

- R1: The extractor produces per-file symbol facts for Python,
  TypeScript/JavaScript (incl. TSX), Go, Rust, Java, C, C++, Zig, Kotlin,
  OCaml, Haskell, and Bash: every definition carries kind (small closed
  enum), name, qualified symbol path (C1), syntactic signature text,
  docstring (C8), full span and identifier span (line:col), parent
  containment, body content hash (C2), and the identifier-excised body
  token set (C2's byte basis, tokenized — the R13 tree-diff score input,
  persisted in the index so a vanished anchor remains scorable). Facts for
  a file derive from that file's content alone. A file that fails to
  parse cleanly (tree-sitter reports an ERROR at or near the root) yields
  best-effort facts from recoverable subtrees and is marked parse-failed
  in the index.
- R2: `ctx sync` updates the index incrementally: an mtime+size scan (or
  the VCS adapter's change feed) proposes candidates, content hashes
  confirm, and only genuinely changed files re-parse. Files whose mtime
  falls within the filesystem's timestamp granularity of the previous
  sync are always re-hashed (racy-edit guard), so a same-size same-mtime
  edit cannot be missed. The baseline scan detects deletions by diffing
  the scanned file set against the indexed set: a removed file's facts
  are purged and its notes' freshness re-derives (anchor unresolvable →
  stale). Every sync appends a
  journal record (C5). `ctx sync --stats` reports files scanned, hashed,
  and parsed; after editing the content of exactly one file in a synced
  fixture, parsed == 1 and hashed == 1; a pure mtime bump with unchanged
  content yields parsed == 0.
- R3: Every query command runs the staleness sweep first (skippable with
  `--no-sync`; skipped automatically when a sync already holds the lock,
  per C6), so query results reflect the working tree as of the last
  completed sync. Note-reading commands (`ctx notes`, `ctx notes list`)
  are query commands for this requirement's purposes.
- R4: The index respects ignore rules: the VCS adapter's ignores when
  present (`.gitignore` under git), plus `.ctxignore` in the no-VCS
  baseline; `.context/cache/` is never indexed.
- R5: The VCS adapter interface isolates change feeds, ignore rules,
  snapshot identity, user identity, and hook points. v1 ships the git
  adapter and the no-VCS baseline; the baseline path (root discovery per
  C4, ignores per R4) works in a plain directory that has never seen
  version control.

Queries (all: compact plain text by default, `--json` variant, never more
data than asked; `<symbol>` arguments resolve per C3; `--doc` renders
docstrings at the depth appropriate to the command — full text on the
single-symbol `ctx sig`, first line on the multi-symbol tree/map
surfaces; a query over an empty or symbol-less scope prints empty output
and exits 0):

- R6: `ctx tree <path> [--depth N] [--limit N] [--doc]` prints the
  containment outline of the requested subtree only, honoring the depth
  cap AND a result cap (default 200 symbols); truncation appends one line
  naming the count omitted and the flag to raise. `--doc` appends each
  symbol's first docstring line to its outline entry. Symbols carrying
  notes get the C10 marker.
- R7: `ctx sig <symbol>` prints the signature, first docstring line, and
  the C10 marker when notes exist; `--doc` adds the full docstring.
- R8: `ctx map [--tokens N] [--doc]` prints a ranked overview: symbols
  ordered by reference-graph importance, truncated to the token budget
  (default 1000, counted per C7), with C10 markers. `--doc` appends first
  docstring lines, counted within the same budget.
- R9: `ctx deps <path> [--reverse]` prints module-level import edges into
  or out of the requested path.
- R10: `ctx refs <symbol> [--limit N]` prints definitions and references,
  each result labeled `heuristic` (global-name match) or `precise`
  (LSP-resolved), capped at 50 results per direction by default with a
  truncation count line naming the flag to raise. Heuristic matching is
  scope-aware where the grammar has locals queries: a reference bound to
  a local definition by `@local.scope`/`@local.definition` analysis
  (per-file, deterministic) is excluded from cross-file candidates;
  languages without locals queries fall back to plain name matching.
- R11: LSP enrichment is optional and additive: with a configured language
  server available, an enrichment pass stores resolved signatures and
  upgrades `ctx refs` results to `precise`; with none, every query still
  works from syntactic facts alone.
- R19: `ctx at <file>:<line>` resolves a position to its innermost
  enclosing symbol and prints the containment chain (module → … →
  innermost) with each symbol's kind, qualified path, signature first
  line, first docstring line, and C10 marker; a position enclosed by no
  definition resolves to
  the file's module symbol. A file the index skips (ignored, unsupported
  extension) or that does not exist prints one line naming the reason and
  exits 4 — stack traces routinely point at generated or ignored files,
  and `ctx at` fails fast rather than guessing. This is the
  stack-trace/test-failure entry point: file:line in, symbol out.
  (Numbered out of sequence to keep existing requirement references
  stable.)

Notes:

- R12: `ctx notes add <symbol> <text> [--kind
gotcha|invariant|rationale|todo]` (body from the positional argument, or
  `--file <path>`, or stdin via `--file -`) writes one ULID-named markdown
  file under `.context/notes/` with YAML frontmatter: id, anchor qualified
  path (C1), anchor body hash (C2), optional kind, author and created
  (C9). Freshness (`fresh`/`stale`) is a DERIVED flag: fresh iff the
  anchor path resolves AND the frontmatter anchor hash equals the current
  body hash — computable from the note file plus the working tree alone,
  so it survives any index rebuild; it is cached in the index and
  returned with every note read. An agent revalidating a stale note
  updates the body and/or refreshes the anchor hash; that is the only
  path that writes the hash after creation. `ctx notes <symbol>` prints that symbol's
  notes with their freshness; `ctx notes list [--kind K] [--stale]
  [--file <path>]` filters on freshness, kind, or the file containing
  the anchored symbol. A note file with unparseable or incomplete frontmatter
  is skipped with one diagnostic line (path + reason); it never aborts a
  query or sync.
- R13: Re-anchoring is deterministic and layered: when an anchored symbol
  no longer resolves, sync re-anchors via qualified-name match (a unique
  definition sharing the anchor's terminal name and kind among the
  changed files' new symbols; zero or multiple candidates → next layer),
  then body-hash match (C2), then tree-diff matching — candidates are
  definitions of the same kind in the changed files' new trees; the score
  is token overlap between identifier-excised body texts (C2's byte
  basis, tokenized); the note re-anchors to the highest-scoring candidate
  above threshold 0.6, ties broken by lowest file:line; with no candidate
  above threshold the note stays un-re-anchored and stale. Tree-diff
  scoring reads the anchor's persisted token set (R1) from the index;
  re-anchoring happens at the sync that observes the disappearance —
  after a full index rebuild an anchor that vanished while unsynced is no
  longer re-anchorable and its note stays stale. Re-anchor persistence is
  two-phase. Phase 1: every sync records the re-anchor in the index
  immediately, so queries see the re-anchored state at once. Phase 2: the
  note file's anchor PATH in frontmatter — the only write the system ever
  makes to a note file — is updated only at explicit persistence points:
  the pre-commit hook installed by R16 (which writes pending anchor
  updates and stages them, so the re-anchor lands in the same commit as
  the refactor that caused it) or an explicit `ctx sync
--write-anchors`. Query-triggered and background syncs never modify
  tracked files. Pending unwritten anchor updates are named in
  `ctx notes list` output and the journal (C5). The anchor HASH is never
  system-written after creation, so a body change stays visible as
  staleness (R12's derivation) until an agent revalidates. When the
  anchored body's hash changes, the note's derived freshness becomes
  stale with a pointer to what changed. Re-anchoring never fires against
  the symbols of a parse-failed file (R1): they are unresolved-transient,
  not vanished — notes anchored there derive stale for the duration
  (R12's rule applies unchanged), their anchor bindings stay untouched,
  and freshness re-derives fresh when the file parses again. Note bodies are never modified
  and note files never deleted by the system; content revalidation is the
  reading agent's job.
- R14: Notes merge under plain VCS semantics: one file per note, so
  concurrent edits to the same note surface as an ordinary merge conflict
  and nothing else conflicts. Anchor-path updates ride the same commit as
  the refactor that caused them (R13 phase 2), so a source refactor may
  legitimately include note-file changes — an expected, reviewable
  effect with the same file-level merge semantics.

Surface and integration:

- R15: An MCP server exposes the same query and note verbs as typed tools,
  as a thin wrapper over the CLI core (no second implementation of query
  logic).
- R16: `ctx hooks install` installs opt-in hooks: pre-warm VCS hooks
  (git's post-checkout/post-merge/post-commit in v1) and a printed snippet
  for a harness PostToolUse hook, each running `ctx sync` in the
  background (journaled per C5) — the PostToolUse snippet additionally
  runs `ctx notes list --file <edited-file>` and emits any output as
  hook additional context, pushing note presence to the agent at edit
  time (the second C10 channel) — plus a pre-commit hook that writes
  pending anchor updates (R13 phase 2) and stages the touched note files
  — writing a given update only when the re-anchored NEW path's file is
  itself in the staged set (a partial commit that leaves the moved-to
  file unstaged leaves that update pending rather than staging an anchor
  to an uncommitted symbol). Hook files are managed as delimited
  blocks: install appends a marked `ctx` block to an existing hook file
  (creating an executable file only if absent), preserving all existing
  content; `ctx hooks uninstall` removes exactly that block and deletes
  only files `ctx` itself created. Under git, install also enables
  `core.fsmonitor` when the git version supports the builtin monitor —
  the staleness scan's scaling path at 100k files — reporting
  enabled/skipped in its output; uninstall reverts only settings it set.
- R17: A README in `context-tree/` documents install, `ctx init`, the
  query surface, the note format, and the documented check command that
  runs the component's full test suite — plus the v1 adoption story
  (CUJS.md CUJ0): a copy-paste integration snippet for a consuming repo's
  CLAUDE.md/AGENTS.md routing structure questions to `ctx` before file
  reads or scout dispatch — delimited by the literal marker
  `ctx-integration-snippet` so installers and the adoption criterion can
  locate it — and MCP registration instructions.
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
- Sync-journal rotation/compaction — the journal lives in deletable
  derived cache; growth management is post-v1.
- Runtime dylib loading of custom tree-sitter grammars (ast-grep's
  `sgconfig.yml` registry pattern) — the post-v1 path for language 13+;
  v1 ships the 12 built-in grammars only.
- Unicode identifier normalization — C2 and C1 operate on raw source
  bytes; no NFC/NFKC folding in v1.

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
      source file — the `typescript/` dir holding a `.ts`, a `.tsx`, and a
      `.js` file — and the check command's output emits one
      `covered: <language>` line per language the R1 suite actually
      enumerated; the criterion checks that output with a whole-line match
      per language (`grep -Fx "covered: <language>"`), so `covered: cpp`
      cannot satisfy the `c` check and a hardcoded subset fails
      mechanically.
- [ ] The documented check command (R17) runs the component's test suite
      green, covering R1 (per-language extraction tests incl. a C++
      overload fixture whose two overloads yield DISTINCT C1 paths that
      each resolve via C3 — asserted as a property, not a self-generated
      snapshot — and a C2 test proving a pure rename leaves the body hash
      unchanged; every language fixture contains at least one documented
      symbol whose docstring embeds a per-fixture sentinel string the
      assertion matches — C8's native conventions, incl. the
      leading-comment rule for C/Zig/Bash), R4 (ignored file
      excluded from index), R5 (index builds in a fixture directory with
      no `.git`), R6–R10 (query output golden tests incl. depth and
      result caps with truncation-count lines, C7 token budget, `--doc`
      first-docstring rendering in tree and map, `ctx sig --doc` printing
      a ≥2-line docstring in full where the default prints only its first
      line, C3 ambiguous-suffix exit code 3, and `heuristic`/`precise`
      labels), R19 (`ctx at` on a line inside a
      nested function prints the containment chain; a line outside any
      definition resolves to the module symbol; an ignored or
      unsupported-extension file exits 4 with a reason), R12 (note file
      format,
      C9 fields normalized in snapshots), R14 (two divergent copies of
      one note file produce a VCS conflict, nothing else), and R18 (init
      idempotence).
- [ ] Incrementality (R2/R3): e2e test syncs a fixture, edits the content
      of one file, and asserts `ctx sync --stats` reports parsed == 1 and
      hashed == 1; a pure mtime bump yields parsed == 0; a query without
      `--no-sync` reflects the edit, and the same query with `--no-sync`
      still shows the pre-edit state.
- [ ] Ranking is real (R8): on a fixture where symbol A is referenced by
      ≥3 other symbols, symbol B by none, and lexical order would place B
      first, `ctx map` ranks A strictly above B — importance provably
      differs from alphabetical or insertion order.
- [ ] Markers on every surface (C10): a symbol carrying one fresh and one
      stale note shows `[notes:2!]` in each of `ctx tree`, `ctx sig`,
      `ctx map`, and `ctx at` output — four asserted surfaces.
- [ ] Mid-edit robustness (R1/R13): given a fixture file with a
      mid-function syntax error, sibling symbols in the same file still
      list, `ctx at` on the broken span resolves to the module fallback
      without error, a note anchored to an untouched sibling keeps its
      freshness, and no re-anchoring fires for the parse-failed file; a
      note anchored to the BROKEN symbol reads stale while broken with
      its anchor binding untouched, and re-derives fresh after repair;
      repairing the error restores full facts on the next sync.
- [ ] `--json` everywhere: for each of tree/sig/map/deps/refs/at, the
      `--json` variant pipes through `jq .` with exit 0 and contains an
      asserted key for that verb's payload.
- [ ] Suffix semantics (C3): in a fixture defining both `app.Handler` and
      `app.AuthHandler`, `ctx sig Handler` exits 0 and resolves to
      `app.Handler` (a substring matcher would exit 3 here), and a
      no-match argument exits 1.
- [ ] Scope-aware refs (R10): in a typescript fixture (a grammar with
      locals queries) where a function-local variable shadows a global
      function's name, `ctx refs <global>` excludes the shadowed local
      references and still lists the true cross-file call site.
- [ ] Note plumbing (R12/C9): `ctx notes list --file <path>` returns
      exactly the notes anchored to symbols in that file;
      `ctx notes add <sym> --file body.md` and
      `printf ... | ctx notes add <sym> --file -` produce notes whose
      bodies match their sources; with `CTX_AUTHOR=x` set the frontmatter
      records `author: x`, and in a no-VCS fixture with it unset,
      `author: unknown`; a note file with corrupted frontmatter yields
      one diagnostic line, is skipped, and the query still exits 0.
- [ ] Concurrency (C6): with the sync advisory lock held by a helper
      process, a query returns within a bounded time, appends no sync
      record to the journal, and serves the last-completed snapshot.
- [ ] Deletion (R2): in a no-VCS fixture, deleting an indexed file that
      carries a note purges its symbols from `ctx tree` on the next sync
      and the note's freshness reads stale.
- [ ] Rebuild equivalence (C4, CUJS.md CUJ11): capture `ctx map`,
      `ctx tree`, and `ctx sig` outputs, delete `.context/cache/`,
      re-query — byte-identical; separately, tampering the cache's
      schema-version field triggers a transparent rebuild — the
      post-tamper journal record shows parsed == the full indexed file
      count — and the same query succeeds.
- [ ] Re-anchoring (R13), all layers: (d) move a function to another file
      WITHOUT rename or edit in a file-is-module language (C fixture —
      the C1 module component changes with the file) → re-anchors via
      qualified-name match (layer 1), freshness fresh; by contrast the
      same move in a Go fixture (module = package) leaves the anchor path
      unchanged with NO pending write — identity survives and only the
      query-reported file:line updates; (a) rename a function in-file
      → queries show the re-anchored note immediately (index phase),
      derived freshness reads fresh, and the note FILE is unchanged until
      a persistence point; (b) edit the function body → freshness reads
      stale, pointer present, note file unchanged; (c) move a function to
      a different file, rename it, AND make a small body edit in the same
      sync → note re-anchors via tree-diff and freshness reads stale.
      After leg (c) and before persistence, the latest journal record
      shows `pending_reanchors` ≥ 1. Then run `ctx sync --write-anchors`:
      the leg-(d)/(a)/(c) anchor paths land in frontmatter and a
      subsequent sync journals `pending_reanchors` == 0. Then delete `.context/cache/` and re-sync
      (rebuild durability), AND clone the fixture to a fresh directory
      and sync there (clone durability): in both, the leg-(c) note
      resolves to the new symbol and reads stale. In a hooks-installed
      fixture, committing the refactor triggers the pre-commit write and
      the note-file update appears staged in the same commit. Throughout,
      the system's only note-file write is the anchor path at a
      persistence point; bodies are never modified, files never deleted,
      and query-triggered/background syncs leave tracked files untouched.
- [ ] Root guard (C4): in a git fixture with no `.context/`, `ctx map`
      exits 2 and names `ctx init`; running `ctx init` places `.context/`
      at the git root and the same query then succeeds.
- [ ] LSP enrichment (R11): with a language server configured in the test
      environment, `ctx refs` on a fixture symbol returns at least one
      `precise` result; with none, the same query returns `heuristic`
      results and exits 0. If no language server is installable in the
      unattended test environment, the worker marks this criterion
      manual-pending with the reason stated
      (docs/memory/unattended-worker-tool-limits.md) rather than skipping
      silently.
- [ ] MCP (R15): a scripted MCP client lists tools matching the full
      query + note verb set; a `ctx tree`-equivalent call returns output
      byte-identical to the CLI for the same args (cross-check against
      reimplementation); one `ctx notes add`-equivalent write creates the
      note file on disk.
- [ ] Hooks (R16): in a throwaway git fixture whose post-checkout hook
      already contains non-ctx content, `ctx hooks install` preserves that
      content and appends the marked block; a checkout then produces a
      `trigger: hook` record in the sync journal (C5) within a bounded
      poll (≤10s); install's output reports the fsmonitor decision
      (enabled, or skipped with reason); the printed PostToolUse snippet
      invokes `ctx notes list --file` (the edit-time note push, R16); a
      partial commit that stages a
      refactor's moved-FROM file but not its moved-TO file leaves the
      anchor update pending rather than staged (R16's partial-commit
      rule); `ctx hooks uninstall` restores
      the original hook bytes exactly and reverts only settings it set.
- [ ] Adoption (R17, CUJS.md CUJ0): `grep -c "ctx-integration-snippet"
context-tree/README.md` ≥ 2 (the snippet's open/close markers) and
      the README documents MCP registration (target file absent today,
      verified 2026-07-15, so the count cannot pass vacuously).
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
