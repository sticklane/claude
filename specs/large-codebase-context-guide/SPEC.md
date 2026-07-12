# Large-codebase context guide: document, don't build — recommend existing MCP servers over new tooling

Breakdown-ready: true

## Problem

The user's own framing is the thesis: codebase pre-indexing for large
repos "may already be well fleshed out and developed into public github
repos, so the answer might be making sure we integrate with the best fit
of those, rather than new skills here." A `deep-research` pass this
session confirmed it: Anthropic's engineering guidance favors
just-in-time retrieval via lightweight identifiers over heavy
pre-indexing, but explicitly endorses a hybrid (some upfront retrieval +
autonomous exploration) where latency matters
(anthropic.com/engineering/effective-context-engineering-for-ai-agents).
Aider's repo-map (tree-sitter parsing + PageRank-style ranking + a
~1k-token signature-only view) is the best-documented reference design
(aider.chat/2023/10/22/repomap.html). Two mature, third-party MCP servers
are real integration candidates:
`zilliztech/claude-context` (hybrid BM25+dense-vector search, AST
chunking, Merkle-tree incremental re-indexing) and
`trondhindenes/code-index-mcp` (wraps Sourcegraph's Zoekt trigram index
for fast substring/regex search). The official MCP reference-servers repo
(`modelcontextprotocol/servers`) ships nothing for code search/indexing at
all. This toolkit's own `scout` agent (`.claude/agents/scout.md`) is
deliberately restricted to `Read, Grep, Glob, Bash(git log/show/ls/wc)` —
cheap and fast by design — and should **stay that way**; nothing here
proposes widening its tool grant.

## Solution

Document, don't build. A new guide,
`docs/guides/large-codebase-context.md`, following the existing
`docs/guides/*.md` pattern (cites primary sources, has a `Verified:` date
per `specs/idea-research-freshness`'s convention if that spec has landed),
covering: Anthropic's JIT-vs-hybrid guidance, Aider's repo-map as the
reference design, and a decision table between the two MCP servers (when
semantic/fuzzy search on a large, actively-changing repo matters, vs. when
fast literal/regex search is enough) — with plain install instructions,
since both are **user-installed, optional, third-party MCP servers**, not
something this toolkit bundles or depends on.

One line is added to `.claude/rules/token-discipline.md`'s "Delegation
defaults" section (cite the guide, don't restate it): when a codebase is
large enough that repeated `scout` dispatches aren't converging on a
fuzzy/semantic query, and a code-search MCP server happens to be
connected this session, reach for it directly (via `ToolSearch`, the same
discovery pattern already used for deferred/MCP tools) instead of more
`scout` rounds — advisory, conditional on "happens to be connected,"
never a hard dependency. `scout.md`'s `tools:` grant is **not** touched —
this preference lives one layer up, in the orchestrating session's own
judgment, exactly so the plugin behaves identically whether or not a user
has an MCP code-search server installed.

## Requirements

- **R1**: `docs/guides/large-codebase-context.md` is created, citing:
  the Anthropic JIT/hybrid-retrieval post; Aider's repo-map blog post;
  both MCP servers' own README claims (hybrid search + AST chunking +
  incremental reindex for `claude-context`; Zoekt-backed fast search for
  `code-index-mcp`); and the finding that no official MCP reference server
  covers this. Each claim carries its URL.
- **R2**: The guide's decision table gives at least two concrete
  "when to reach for which" rows (e.g. "need semantic/fuzzy search across
  a large, frequently-changing repo → `claude-context`"; "need fast
  literal/regex search, no semantic layer needed →
  `code-index-mcp`") plus a "neither — repo is small/medium, scout's
  grep/glob is enough" row, so a reader isn't left thinking either MCP
  server is always necessary. The guide also includes at least one
  non-empty ```mermaid fence — a small decision-flow diagram (repo size →
  grep-enough? → semantic-need? → which server) — required by this
  repo's own link-checker gate (`tests/test_doc_links.sh` hard-fails any
  `docs/guides/*.md` file with zero mermaid fences; all three existing
  guides already carry one, so this isn't a new pattern, just one this
  spec must not skip).
- **R3**: `.claude/rules/token-discipline.md`'s "Delegation defaults"
  section gains one new bullet, and it must name the actor explicitly —
  **the orchestrating session, never `scout` itself** (`scout` cannot
  `ToolSearch`; nothing changes for it, per R4): for a large codebase
  where repeated `scout` dispatches on a fuzzy/semantic query aren't
  converging, the orchestrating session runs a `ToolSearch` for a
  connected code-search MCP tool — this probe IS how it learns whether
  one is connected, not a precondition it can check passively — and if
  one turns up, prefers it over further `scout` rounds. Cites
  `docs/guides/large-codebase-context.md`, doesn't restate its content.
- **R4**: `.claude/agents/scout.md`'s `tools:` frontmatter is **unchanged**
  — this spec does not widen scout's tool grant; the MCP preference is
  the orchestrating session's judgment call, not scout's.
- **R5**: Nothing in this spec adds a runtime dependency on either MCP
  server — every existing skill/agent continues to function identically
  in a session with neither installed. This is the plugin's own
  "works with or without additional [MCP] skills installed" requirement.

## Out of scope

- Bundling, installing, or configuring either MCP server as part of this
  plugin — both stay user-installed, optional, external tools; this spec
  only documents when a user might want one.
- Building any new indexing/repo-map tooling in this toolkit — explicitly
  rejected per the Problem section's research finding (integrate with
  existing prior art, don't reinvent it).
- Widening `scout.md`'s tool grant, or creating a second, MCP-aware scout
  variant — R4.
- A mechanical check that the guide's claims stay current (that's
  `specs/idea-research-freshness`'s `Verified:` convention, applied here
  like any other `docs/guides/*.md` page — not re-specified in this spec).

## Acceptance criteria

- [ ] `docs/guides/large-codebase-context.md` exists, citing the Anthropic
      post, Aider's repo-map post, and both MCP servers' READMEs, each
      with its URL.
- [ ] The guide's decision table has at least the three rows from R2
      (semantic/fuzzy-large-repo, fast-literal-search, neither-needed),
      and the guide contains at least one non-empty mermaid fence (R2).
- [ ] `.claude/rules/token-discipline.md` contains the new bullet from R3,
      citing the guide rather than restating it.
- [ ] `diff .claude/agents/scout.md` (before/after this spec) shows no
      change to the `tools:` frontmatter line (R4).
- [ ] `bash tests/test_doc_links.sh` passes with the new guide included.
- [ ] End-to-end: a human reading the new guide can, without further
      research, decide whether their current project warrants installing
      `claude-context`, `code-index-mcp`, neither, and how to install
      whichever they pick.

## Open questions

(none)

## Parallelization

This spec decomposes into a single task (task 01: the guide plus the
token-discipline bullet are one cohesive, decision-coupled deliverable — the
rule bullet cites the guide, so it cannot be authored before the guide's
content is settled). Task 01 runs solo; there are no concurrent-safe groups.
