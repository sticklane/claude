# Codebase context tree — research and architecture

Research and design groundwork for a new toolkit component: a queryable,
always-in-sync structural map of a repository — a symbol tree with
signatures, docstrings, positions, and agent-attached notes — maintained
deterministically (no model calls) and consumed by agents through a compact,
ask-only-get-only query surface. The core thesis: code should be
self-documenting, but context windows make whole-file reading the wrong
default; agents need a compact representation of a repo's what and how that
they can query and annotate.

Status: research complete, the major architecture forks decided with the
maintainer (2026-07-15), spec not yet written. The remaining open questions
are at the end; the spec (`specs/codebase-context-tree/SPEC.md`) follows
once they are resolved.

## Table of contents

Decisions taken · Research: unify at the symbol level, not the AST ·
Research: what existing agent-facing tools do · Research: incremental sync
and node identity · Research: notes that survive refactorings ·
Architecture sketch · How this fits existing doctrine · Open questions ·
Primary sources

## Decisions taken (maintainer interview, 2026-07-15)

| Fork              | Decision                                                                                                                                                                                                                                                                                               |
| ----------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Data model        | Universal **symbol tree** (not a universal AST), extracted per-file by tree-sitter with per-language symbol queries; optional LSP (Language Server Protocol) enrichment adds resolved types where a server is available.                                                                               |
| Sync trigger      | Hybrid: file-change-driven is primary; a passing build/typecheck additionally stamps nodes validated and refreshes LSP enrichment.                                                                                                                                                                     |
| Sync architecture | Lazy sync-on-query plus hook pre-warming. No always-on daemon.                                                                                                                                                                                                                                         |
| Note behavior     | Deterministic re-anchoring; content-hash change flags a note stale; the next agent that reads it revalidates. Maintenance itself never spends tokens.                                                                                                                                                  |
| Note storage      | In-repo version-tracked files (one file per note); the queryable index is a derived, ignored cache.                                                                                                                                                                                                    |
| Query surface     | CLI core returning compact plain text (JSON behind a flag); MCP server as a thin wrapper over the same core.                                                                                                                                                                                           |
| V1 scope adds     | Import/dependency edges, cross-file def/ref edges, ranked overview (Aider-style, token-budgeted). Semantic/vector search is out.                                                                                                                                                                       |
| Scale posture     | V1 targets 100k files with headroom to 100M: no sync or query path may assume whole-tree enumeration; change detection and storage must be shardable.                                                                                                                                                  |
| V1 languages      | Python, TypeScript/JavaScript (incl. TSX), Go, Rust, Java, C, C++, Zig, Kotlin, OCaml, Haskell, Bash. Several of these grammars are community-maintained and lack upstream symbol queries, so authoring per-language query files is part of the build cost.                                            |
| VCS coupling      | No single version-control system assumed: the baseline staleness sweep is plain filesystem mtime+hash and works with no VCS at all; VCS integrations (change feeds, ignore rules, snapshot identity, hooks) are pluggable accelerator adapters behind one interface. Git is the only adapter v1 ships. |

The rationale for each decision is the research below.

## Research: unify at the symbol level, not the AST

Verified: 2026-07-15

The original framing — "a language-agnostic AST data model, plus AST support
for every commonly used language" — points at a graveyard. Every attempt to
unify the AST (abstract syntax tree) itself is dead or frozen: Babelfish/UAST's docs domain no
longer resolves and its "semantic" canonicalization died unfinished with
sponsor source{d}; srcML covers exactly four C-family languages after ~20
years; OMG's ASTM standard was adopted at v1.0 in January 2011, never
revised, and its own architecture concedes the point by splitting into a
generic core (GASTM) plus per-language escape hatches. The failure mode is
structural: an AST's value is exactly its language-specific detail, so a
universal schema either grows an unmaintainable union of all constructs or
normalizes that detail away — and the mapping burden lands O(languages ×
constructs) on one central team.

Every surviving cross-language system unifies one level up, at the
symbol/outline layer, and leaves expression-level structure to per-language
grammars:

| System                 | Unified artifact                                                 | AST exposed?                       |
| ---------------------- | ---------------------------------------------------------------- | ---------------------------------- |
| tree-sitter `tags.scm` | `@role.kind` captures (~8 categories) + `@name`                  | Tree exists but is per-grammar     |
| LSP `DocumentSymbol`   | 26 SymbolKinds, name, two ranges, children                       | No AST in the protocol             |
| SCIP (Sourcegraph)     | `scheme package descriptor+` symbol strings, ~8 descriptor kinds | No                                 |
| Kythe (Google)         | Semantic graph of defs/refs                                      | No — compilers emit semantic facts |
| ctags                  | name + file + per-language kind                                  | No                                 |

tree-sitter itself ("general enough to parse any programming language …
efficiently update the syntax tree as the source file is edited",
tree-sitter.github.io) is the proven parsing substrate with grammars for
effectively every mainstream language, but its node vocabulary is
per-grammar by design. The cross-language layer is the query convention on
top: each grammar ships `queries/tags.scm` mapping its own nodes onto a tiny
shared capture vocabulary (`@definition.function`, `@definition.class`,
`@reference.call`, …). That convention — per-language trees, one shared
symbol taxonomy above them — is the data model this project adopts.

A second consequence of AST-only extraction: signatures are syntactic. A
pure parse of `def f(x, y):` yields no types. Resolved types require the
language's own type checker or LSP server, which is why the decision keeps
tree-sitter as the universal base and treats LSP-derived type/hover
enrichment as optional, additive, and never load-bearing for the tree's
existence.

## Research: what existing agent-facing tools do

Verified: 2026-07-15

Three architecture tiers exist among tools that give agents codebase
structure. First, ranked plain-text outlines: Aider tree-sitter-parses every
file's definitions, builds a dependency graph, runs "a graph ranking
algorithm, computed on a graph where each source file is a node and edges
connect files which have dependencies," and renders only "the most important
identifiers, the ones which are most often referenced" into a token-budgeted
(`--map-tokens`, default 1k) outline sized "dynamically based on the state
of the chat" (aider.chat/docs/repomap.html). RepoGraph is the academic
analogue and "substantially boosts the performance of all systems" it plugs
into on SWE-bench (arxiv.org/abs/2410.14684). Second, embedding indexes over
AST-aware chunks: Cursor "breaks your code into meaningful chunks
(functions, classes, logical blocks)" into a vector store with 5-minute
changed-file sync; Zilliz's claude-context does AST chunking with "hybrid
search (BM25 + dense vector)" and re-indexes "only changed files using
Merkle trees." Third, agent-queried graph databases: CodexGraph "integrates
LLM agents with graph database interfaces," Greptile "builds a complete
graph of your repository containing every code element," Potpie builds a
"living context graph." Serena takes a fourth, LSP-shaped route: symbol-level
MCP tools (symbol overview, find symbol, find referencing symbols) so agents
explore "without reading entire files."

Two lessons carry over directly. Extraction is easy; selection under a token
budget is the differentiator — Aider's graph ranking, GraphCoder's
coarse-to-fine retrieval, and Agentless's tree → skeleton → code narrowing
all converge on progressive disclosure rather than structure-dumping. And on
format: storage can be protobuf, SQLite, or a graph DB, but every surveyed
tool hands the model compact plain text. No tool feeds raw JSON graphs into
context, and Aider's write-side benchmark found "LLMs produce lower quality
code if they're asked to return it as part of a structured JSON response"
(aider.chat/2024/08/14/code-in-json.html) — read-side format studies are
absent, but the convergent practice is unanimous.

## Research: incremental sync and node identity

Verified: 2026-07-15

The requirement "updates should only deal with code that has changed, never
the entire repo tree" has a proven blueprint: GitHub's stack-graphs team
states it as a design law — "we look at each file completely in isolation"
at index time, because otherwise "we'll have to reanalyze every file in the
repository … whenever any file changes"; cross-file resolution happens at
query time by stitching per-file results (github.blog, "Introducing
stack graphs"). Production indexers detect change by content hash: Cursor
syncs "every 5 minutes, processing only changed files"; claude-context
re-indexes "only changed files using Merkle trees." tree-sitter adds
sub-file reuse but only given explicit edit deltas (an editor buffer, not a
disk event), and its own docs warn that stored node positions are
invalidated by every edit — Roslyn's red-green trees teach the same lesson
from the compiler side ("every node tracks its width but not its absolute
position", ericlippert.com/2012/06/08/red-green-trees). Positions are
therefore per-snapshot display data, never identity.

On identity, no single scheme survives every refactoring:

| Scheme                         | Survives rename                                               | Survives file move                                          | Survives body/signature edit |
| ------------------------------ | ------------------------------------------------------------- | ----------------------------------------------------------- | ---------------------------- |
| Qualified-name ID (SCIP-style) | no                                                            | yes, when the language's qualified name is path-independent | yes (name-only)              |
| Content hash (Unison-style)    | yes — "names are just separately stored metadata"             | yes                                                         | no                           |
| Position (path + span)         | no                                                            | no                                                          | no                           |
| Tree-diff matching (GumTree)   | recovers it post-hoc — "can detect moved or renamed elements" | yes                                                         | often                        |

Robust systems layer these: a stable-ish semantic ID, plus a content hash,
plus diff-based matching as the fallback that re-links what the first two
lose. That layering is what the architecture below adopts, and it is also
exactly what note re-anchoring needs.

## Research: notes that survive refactorings

Verified: 2026-07-15

The mature prior art is code review, not agent tooling. Gerrit stores a
comment against its original patchset and, at view time, "tries to calculate
the position of this comment on the new version of the file," degrading
gracefully — unmappable comments become file-level comments, and in extreme
cases (a reverted file) the comment is not ported but survives at its
original location (gerrit-review.googlesource.com, user-porting-comments).
GitHub stores `original_commit_id`/`original_line` alongside a recomputed
position and flags rather than heals: "Not using the latest commit SHA may
render your comment outdated if a subsequent commit modifies the line"
(docs.github.com/en/rest/pulls/comments). CodeTour makes the author pick the
anchor: ordinal line, captured span, a content regex ("associate steps with
line content as opposed to ordinal"), or a pin to an immutable git ref that
"will never get out of sync." Staleness detection is its own literature —
Fraco (ASE 2017) detects comments "fragile with respect to identifier
renaming," and later work does "just-in-time" inconsistency detection
triggered by the diff rather than by snapshot scans.

The gap this project fills: every AI-agent memory system surveyed — Claude
Code's directory-scoped CLAUDE.md and glob-scoped rules, Cursor's
`.cursor/rules` globs, Serena's project-scoped memories — anchors at
directory/glob/repo granularity, never to a symbol or span, and handles
staleness advisorily ("review … periodically to remove outdated
instructions"). The span-anchor + diff-remap + outdated-flag machinery
proven in review tools has not migrated to agent memory. Symbol-anchored
notes with deterministic re-anchoring and stale-flagging are the novel part
of this design; the pieces are individually proven.

Two framing corrections this research forced on the original idea. "Notes
should self-update as needed" and "maintenance must not require any token
usage" conflict — judging whether a note is still true after code changed is
judgment work. The resolution (decided above): the deterministic layer
re-anchors positions and flags staleness with a diff pointer; the semantic
layer — actually rewriting a stale note — runs lazily, by the next agent
that reads the note, as part of work already paying for that context. Token
spend attaches to reads that were happening anyway, and the maintenance path
itself stays model-free.

## Architecture sketch

Proposed shape for the spec; component names are placeholders.

**Components.** An extractor (tree-sitter grammars + per-language symbol
queries in the `tags.scm` style) turns each file into per-file facts:
definitions with kind/name/signature-text/docstring/spans, references,
imports. Facts for a file depend on that file alone — the stack-graphs
isolation rule — so one edit never fans out. A derived store (SQLite,
gitignored, rebuildable from scratch) indexes files (path, content hash),
symbols, and edges. A note store holds git-tracked note files. One CLI
(working name `ctx`) owns sync and queries; an MCP server wraps the same
core for harnesses that prefer typed tools; a harness PostToolUse hook and
VCS hooks (git's post-checkout/post-merge/post-commit in v1) pre-warm sync
so interactive queries rarely pay it.

**Node schema (per symbol).** Stable ID (qualified symbol path), kind (small
closed enum in the LSP SymbolKind spirit, ignore-unknown rule), name,
syntactic signature text, docstring (first line stored inline, full text on
demand), file + full span + identifier span (line:col, snapshot-scoped),
parent/children, language, body content hash, optional LSP enrichment
(resolved signature, validated-at commit).

**Sync path (lazy).** Every query begins with a staleness sweep: an
mtime-size scan (or the VCS adapter's change feed, where one is available)
proposes candidates, content hashes confirm real changes, and only genuinely changed files re-parse (tree-sitter parses at
milliseconds per file). Cost is bounded by the number of changed files,
never repo size. Cross-file products (ref resolution, ranking) recompute at
query time or from caches invalidated by the per-file fact versions they
read. The worst case — first query after a large pull — pays a burst that
hooks exist to pre-warm; between queries the system does nothing at all,
which is the answer to the watcher-per-keystroke performance trap.

**Scale posture.** V1 targets 100k files; the design keeps headroom for
100M. Three rules follow. Change detection layers over a VCS-agnostic
baseline: the plain mtime+hash sweep needs no version control at all, and
VCS adapters accelerate it behind one interface. V1 ships only the git
adapter — `git status --porcelain` already respects ignore rules, and with
`core.fsmonitor` (Watchman-backed) git scales status checks to monorepo
size; git's object model is itself a Merkle tree, so its change feeds
replace custom whole-tree hashing. The ecosystems that actually operate at
100M files (Sapling/EdenFS, Perforce) plug in as additional adapters
rather than forcing a redesign. Storage
shards: one SQLite file is right at 100k files, but per-file facts (the
stack-graphs isolation rule) partition naturally, so the store splits by
directory subtree without a design change. Queries stay subtree-scoped by
default, and the ranked overview reads precomputed per-shard rank rollups
rather than running graph ranking over the whole repo at query time.

**Note lifecycle.** A note anchors to a symbol ID plus the anchored symbol's
body hash, stored as one small markdown file with YAML frontmatter (id,
anchor, hash, author, created, status) under a directory like
`.context/notes/`. On sync: anchor resolves and hash matches → fresh; symbol
path gone → tree-diff matching attempts rename/move re-anchor; body hash
changed → status becomes stale with a pointer to what changed. Notes are
never silently deleted (Gerrit's losslessness). On read: the query returns
the note with its staleness flag; a reading agent confirms, rewrites, or
retires it as part of its normal task. Because notes are in-repo files, they
travel with clones and branches, appear in PR diffs for human review, and
merge with rare, trivial conflicts (one file per note).

**Query surface (illustrative).** `ctx map --tokens 1000` (ranked overview),
`ctx tree src/auth --depth 2` (containment outline), `ctx sig
auth.login.authenticate --doc` (signature + docstring), `ctx refs
authenticate` (defs/refs), `ctx deps src/auth --reverse` (import edges),
`ctx notes <symbol>` / `ctx notes add <symbol> <text>`. Output is indented
plain text sized to what was asked — depth caps, token budgets, first-line
docstrings unless `--doc` — with `--json` for scripts. Nothing returns more
than asked for; the compact-overview thesis lives or dies on this.

## How this fits existing doctrine

This tool is the structural complement to the JIT-retrieval default in
`docs/guides/large-codebase-context.md` (verified 2026-07-11): scouts and
grep answer "where is X" by searching content; the context tree answers
"what exists and how is it shaped" without reading files, and gives notes a
place to live that is finer-grained than CLAUDE.md and coarser-grained than
code comments. It does not replace semantic search — the decision table in
that guide still routes fuzzy "find code about X" queries to claude-context.
Maintenance being deterministic keeps it on the right side of
`.claude/rules/token-discipline.md`'s axis: scripts own loops and gates;
models own judgment (here, only note revalidation, at read time).

## Open questions

To resolve before or during the spec; the first two are `/design`-shaped.

1. **Cross-file def/ref resolution strategy.** Heuristic global-name
   matching (Aider-grade: cheap, wrong on shadowing/overloads) vs. the
   stack-graphs library (precise, but needs per-language stack-graph rules)
   vs. LSP-backed resolution where available with heuristic fallback.
   Leaning: heuristic matching for ranking purposes, LSP for precise refs
   when enrichment is on, precision labeled in output.
2. **Implementation runtime.** Go (matches `agentprof/`, static binary) vs.
   Rust (native tree-sitter) vs. Python (matches the toolkit's scripts,
   slower, environment-dependent). The evaluation must cover binding and
   grammar quality across the full 12-language set — the Zig, Kotlin,
   OCaml, and Haskell grammars are community-maintained.
3. **Note taxonomy and granularity.** Free-form text vs. typed kinds
   (gotcha, invariant, rationale, todo); whole-symbol anchors only (leaning
   yes for v1 — research shows sub-symbol spans are the fragile part) vs.
   span-in-symbol anchors.
4. **Note merge/branch semantics.** One file per note with ULID names
   minimizes conflicts; stale flags recompute per checkout — but concurrent
   edits to the same note body across branches still need a stated policy.
5. **Relationship to `scout`.** Whether toolkit doctrine eventually routes
   structure questions to `ctx` before dispatching scouts, and what that
   changes in `.claude/rules/token-discipline.md`.

## Primary sources

tree-sitter docs (tree-sitter.github.io: parser goals, queries, code
navigation/tags convention) · LSP 3.17 spec, DocumentSymbol/SymbolKind
(microsoft.github.io/language-server-protocol) · SCIP format
(github.com/sourcegraph/scip, docs/scip.md and scip.proto) · Kythe overview
(kythe.io/docs/kythe-overview.html) · ctags man page (docs.ctags.io) ·
srcML (srcml.org) · OMG ASTM (omg.org/spec/ASTM) · Aider repo map
(aider.chat/docs/repomap.html, aider.chat/2023/10/22/repomap.html) and
code-in-JSON benchmark (aider.chat/2024/08/14/code-in-json.html) · Serena
(github.com/oraios/serena) · claude-context
(github.com/zilliztech/claude-context) · Cursor codebase indexing
(cursor.com/docs/context/codebase-indexing) · Greptile
(greptile.com/docs/how-greptile-works) · RepoGraph (arxiv.org/abs/2410.14684)
· CodexGraph (arxiv.org/abs/2408.03910) · GraphCoder
(arxiv.org/abs/2406.07003) · Agentless (arxiv.org/abs/2407.01489) ·
stack-graphs (github.blog/2021-12-09-introducing-stack-graphs) · salsa
(salsa-rs.github.io/salsa) · red-green trees
(ericlippert.com/2012/06/08/red-green-trees) · GumTree
(github.com/GumTreeDiff/gumtree) · Unison
(unison-lang.org/docs/the-big-idea) · Watchman
(facebook.github.io/watchman) · Gerrit ported comments
(gerrit-review.googlesource.com/Documentation/user-porting-comments.html) ·
GitHub PR review comments (docs.github.com/en/rest/pulls/comments) ·
CodeTour (github.com/microsoft/codetour) · Fraco/comment-staleness papers
(ieeexplore.ieee.org/document/8115624, arxiv.org/abs/2010.01625) · Claude
Code memory (code.claude.com/docs/en/memory) · Cursor rules
(cursor.com/docs/context/rules).
