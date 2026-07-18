# Task 11: MCP server

Status: done
Depends on: 07, 09
Priority: P2
Budget: 35 turns
Spec: ../SPEC.md (requirement R15)
Touch: context-tree/src/mcp/**, context-tree/src/cli.rs, context-tree/Cargo.toml, context-tree/tests/*.rs

## Goal

An MCP server (stdio, via the official `rmcp` SDK) exposes the same query
verbs (tree, sig, map, deps, refs, at) and note verbs (notes add, notes,
notes list) as typed tools, as a thin wrapper calling the same CLI-core
functions built in tasks 06/07/09 — no second implementation of query or
note logic. `ctx mcp` (or equivalent subcommand) starts the server.

## Touch

Only `src/mcp/**` (new) and the minimal CLI wiring to launch it. Do not
reimplement any query/note logic here — call into the existing `cmd::*`
functions directly.

## Steps

1. Add the `rmcp` dependency.
2. Implement the stdio MCP server exposing one typed tool per query/note
   verb, each tool's handler calling the corresponding `cmd::*` function
   used by the CLI (not a reimplementation).
3. RED/GREEN: write a scripted MCP client test (a small Rust test harness
   speaking the MCP protocol over stdio, or a scripted JSON-RPC exchange)
   that lists tools and asserts the full query + note verb set is present.
4. RED/GREEN: a `ctx tree`-equivalent MCP tool call on a fixture returns
   output byte-identical to the CLI's `ctx tree --json` for the same args
   (cross-check against the CLI as the reimplementation-avoidance proof).
5. RED/GREEN: one `ctx notes add`-equivalent MCP tool call creates the
   note file on disk (same format as the CLI path).

## Acceptance

- [x] `cd context-tree && cargo test mcp_tool_list` → passes (all
      query + note verbs present as typed tools)
      — verifier: `test mcp_tool_list ... ok`; evidence/11-mcp-server.md
- [x] `cd context-tree && cargo test mcp_tree_matches_cli` → passes
      (byte-identical output vs `ctx tree --json` for the same args)
      — verifier: `test mcp_tree_matches_cli ... ok`; evidence/11-mcp-server.md
- [x] `cd context-tree && cargo test mcp_notes_add_writes_file` → passes
      (note file created on disk via the MCP path)
      — verifier: `test mcp_notes_add_writes_file ... ok`; evidence/11-mcp-server.md
- [x] `bash context-tree/scripts/check.sh` → exits 0
      — verifier: full suite (fmt --check, clippy -D warnings, all tests) exit 0
