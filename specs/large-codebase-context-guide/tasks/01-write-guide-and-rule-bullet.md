# Task 01: Write the large-codebase-context guide and the token-discipline bullet

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers. ## Progress / ## Deferred questions are drain-written sections. -->

Status: in-progress
Depends on: none
Priority: P2
Budget: 10 turns
Spec: ../SPEC.md (requirements R1, R2, R3, R4, R5)
Touch: docs/guides/large-codebase-context.md, .claude/rules/token-discipline.md

## Goal

A new human-facing guide `docs/guides/large-codebase-context.md` exists,
following the existing `docs/guides/*.md` pattern, that documents (not
builds) the large-codebase context-retrieval landscape: Anthropic's
just-in-time-vs-hybrid retrieval guidance, Aider's repo-map as the reference
design, and a decision table between the two mature third-party MCP servers
(`zilliztech/claude-context` and `trondhindenes/code-index-mcp`) plus a
"neither needed" row — with install instructions, since both are optional
user-installed external tools this toolkit never bundles. A single new bullet
in `.claude/rules/token-discipline.md`'s "Delegation defaults" section cites
the guide (does not restate it) and names the orchestrating session — never
`scout` — as the actor that may `ToolSearch` for a connected code-search MCP
tool when repeated scout dispatches on a fuzzy/semantic query aren't
converging. `scout.md`'s `tools:` grant is untouched; no runtime dependency
on either MCP server is introduced.

## Touch

- `docs/guides/large-codebase-context.md` — new file (the guide).
- `.claude/rules/token-discipline.md` — append exactly one bullet to the
  "Delegation defaults" section (line ~7).
- Do NOT touch `.claude/agents/scout.md` (R4 — its `tools:` frontmatter must
  be byte-identical before and after this task).
- No antigravity/codex mirror is required: `.claude/rules/` and
  `docs/guides/` are not mirrored to `antigravity/` (verified — the mirror
  chain covers skills/agents only), so no mirror path and no plugin.json bump
  belong in this task.

## Steps

1. Read the spec's Problem and Solution sections — the deep-research pass is
   already done there; this task transcribes and organizes those findings,
   it does not re-research. Read one existing guide (e.g.
   `docs/guides/model-routing.md`) to match the house format, including how
   it carries a `Verified:` line and a `mermaid` fence.
2. Author `docs/guides/large-codebase-context.md`. It MUST cite, each with
   its URL:
   - Anthropic effective-context-engineering post:
     `https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents`
     (JIT retrieval via lightweight identifiers, endorsing a hybrid where
     latency matters).
   - Aider repo-map post: `https://aider.chat/2023/10/22/repomap.html`
     (tree-sitter parsing + PageRank-style ranking + ~1k-token
     signature-only view — the reference design).
   - `claude-context` README: `https://github.com/zilliztech/claude-context`
     (hybrid BM25 + dense-vector search, AST chunking, Merkle-tree
     incremental re-indexing).
   - `code-index-mcp` README:
     `https://github.com/trondhindenes/code-index-mcp` (wraps Sourcegraph's
     Zoekt trigram index for fast substring/regex search).
   - The finding that the official MCP reference-servers repo
     (`https://github.com/modelcontextprotocol/servers`) ships nothing for
     code search/indexing.
3. Include a decision table with at least these three rows (R2): (a) need
   semantic/fuzzy search across a large, frequently-changing repo →
   `claude-context`; (b) need fast literal/regex search, no semantic layer →
   `code-index-mcp`; (c) repo is small/medium, scout's grep/glob is enough →
   neither. Add plain install instructions for each server.
4. Add at least one non-empty ```mermaid fence — a small decision-flow
   diagram (repo size → grep-enough? → semantic-need? → which server) —
   required by `tests/test_doc_links.sh` (it hard-fails any
   `docs/guides/*.md` with zero mermaid fences).
5. Optionally add a `Verified: <ISO date>` line matching the existing guides'
   convention (the mechanical freshness check is a separate spec; just follow
   the house format).
6. Append exactly one bullet to `.claude/rules/token-discipline.md`'s
   "Delegation defaults" section: when a codebase is large enough that
   repeated `scout` dispatches on a fuzzy/semantic query aren't converging
   and a code-search MCP server happens to be connected this session, the
   **orchestrating session** (never `scout`, which cannot `ToolSearch`) runs
   a `ToolSearch` to discover it and prefers it over further scout rounds —
   advisory, conditional on "happens to be connected," never a hard
   dependency. Cite `docs/guides/large-codebase-context.md`; do not restate
   its content.
7. Run `bash tests/test_doc_links.sh` and confirm it passes with the new
   guide included.

## Acceptance

- [ ] `test -f docs/guides/large-codebase-context.md` → file exists.
- [ ] `grep -Fq 'anthropic.com/engineering/effective-context-engineering-for-ai-agents' docs/guides/large-codebase-context.md && grep -Fq 'aider.chat/2023/10/22/repomap.html' docs/guides/large-codebase-context.md && grep -Fq 'github.com/zilliztech/claude-context' docs/guides/large-codebase-context.md && grep -Fq 'github.com/trondhindenes/code-index-mcp' docs/guides/large-codebase-context.md && grep -Fq 'github.com/modelcontextprotocol/servers' docs/guides/large-codebase-context.md` → all five cited URLs present (exit 0).
- [ ] `grep -cE '^\s*```mermaid' docs/guides/large-codebase-context.md` → ≥ 1 (at least one mermaid fence).
- [ ] `grep -Fq 'large-codebase-context' .claude/rules/token-discipline.md` → the new bullet cites the guide (exit 0).
- [ ] `git diff --quiet HEAD -- .claude/agents/scout.md` → exit 0 (scout.md unchanged this task, R4).
- [ ] `bash tests/test_doc_links.sh` → exits 0 (passes with the new guide).
- [ ] Manual-pending (human, post-merge, AC6): a reader of the new guide can
      decide whether their project warrants `claude-context`,
      `code-index-mcp`, or neither, and how to install the chosen one —
      unattended workers cannot self-verify a human-readability criterion.
