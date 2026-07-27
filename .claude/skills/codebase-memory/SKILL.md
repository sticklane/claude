---
name: codebase-memory
description: Answers code-structure questions with the repository's Codebase-Memory graph before bounded source fallback—architecture, qualified symbols, callers, dependencies, impact, snippets, and coverage-aware negative claims.
---

# Codebase-Memory

Use Codebase-Memory for structural code exploration. It is an index and
navigation aid, not evidence that unchecked source does not exist. Keep graph
responses small, name the active project, and verify negative claims against
index status and bounded direct source.

## Availability and project identity

1. Resolve the active repository to an absolute Git root.
2. Prefer the MCP server named `codebase-memory-mcp`.
3. Call `list_projects` and select the project whose repository root matches
   the active Git root. Never guess from a basename when several projects
   could match.
4. If the project is absent, call `index_repository` for only the active root
   with persistence disabled (`persistence=false`), then poll `index_status`.
   Do not enable automatic indexing or write a shared graph artifact.
5. If MCP is unavailable, try the installed launcher in one-shot CLI mode:
   `agentic-codebase-memory-mcp cli <tool> ...`.
6. If neither interface is available, continue with `rg` plus bounded file
   reads and explicitly say that graph coverage was unavailable. An optional
   backend must not block unrelated work.

Do not call destructive or stateful surfaces such as `delete_project`,
`manage_adr`, or `ingest_traces` during ordinary exploration.

## Progressive query ladder

Use the narrowest sufficient rung and stop when it answers the question:

1. `get_architecture` — orient to the repository without reading whole files.
2. `get_graph_schema` — inspect labels and relationships before a nontrivial
   graph query.
3. `search_graph` — resolve names to qualified symbols and paths. For an
   ambiguous symbol, present the candidates or narrow by path/label; do not
   silently choose one.
4. `trace_path` — start from one resolved `function_name` and choose
   `direction`, `depth`, and `mode` to trace callers, callees, or both. It is
   not a source-to-target path query.
5. `detect_changes` — evaluate the impact of changed or selected symbols.
6. `get_code_snippet` — fetch source only after locating the qualified symbol.
7. `search_code` — answer literal/content questions. When coverage is
   incomplete, use `rg` over a named path set followed by bounded file reads.

Use pagination deliberately. Request a small page, state the limit, and fetch
additional pages only when the claim requires them. Distill returned nodes
into qualified symbols, paths, relationship types, and the coverage fact that
supports the conclusion; do not paste raw graph output.

## Coverage and negative claims

Before saying that a symbol, caller, import, or string is absent:

- Confirm the selected project identity and current `index_status`.
- Account for relevant pagination instead of treating the first page as the
  full result.
- Treat skipped, ignored, unparsed, and unindexed paths as incomplete
  coverage. Record that as "incomplete coverage" and search those candidate
  paths with bounded direct source tools.
- Treat an uncommitted working tree as potentially newer than the graph. Use
  `detect_changes`, inspect the bounded diff, and use bounded direct source
  search over changed paths.
- Treat a graph-empty result as a navigation result, not proof of textual
  absence. Follow with `search_code` and, where needed, a bounded direct
  source search using `rg`.

Report uncertainty when project identity, freshness, pagination, or coverage
cannot be established.

## Failure-boundary recipes

These recipes make the ordering requirements local and testable:

### Ambiguous symbol

`list_projects` → `index_status` → `get_graph_schema` → `search_graph` →
report or narrow the ambiguous symbol candidates.

### Incomplete coverage

`list_projects` → `index_status` → `search_code` → record incomplete
coverage → use bounded direct source search over the named uncovered paths.

### Paginated result

`list_projects` → `index_status` → `search_graph` → account for pagination
until the requested claim is covered.

### Stale uncommitted source

`list_projects` → `index_status` → `detect_changes` → identify the
uncommitted paths → use bounded direct source verification over those paths.

### Graph empty text present

`list_projects` → `index_status` → record that the result is graph-empty →
`search_code` → use bounded direct source verification where text coverage
remains incomplete.

## Parent-to-child handoff

Some child-agent frontmatter cannot safely grant MCP tools. In that case the
parent queries Codebase-Memory first, then includes in the handoff: project
identity, index and coverage state, qualified symbols, relevant paths,
relationship evidence, pagination limits, and any bounded fallback already
performed. The child returns distilled evidence and can use bounded `rg` plus
small reads for gaps; it must not claim complete graph coverage.
