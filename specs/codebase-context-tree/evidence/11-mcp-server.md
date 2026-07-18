# Verification: Task 11 - MCP server

Verdict: PASS

## Acceptance criteria

1. `cd context-tree && cargo test mcp_tool_list` → PASS
   - `test mcp_tool_list ... ok` (1 passed; 0 failed)

2. `cd context-tree && cargo test mcp_tree_matches_cli` → PASS
   - `test mcp_tree_matches_cli ... ok` (1 passed; 0 failed)

3. `cd context-tree && cargo test mcp_notes_add_writes_file` → PASS
   - `test mcp_notes_add_writes_file ... ok` (1 passed; 0 failed)

4. `bash context-tree/scripts/check.sh` → PASS
   - Ran to completion, `EXIT: 0`. Full suite (fmt --check, clippy -D
     warnings, all integration tests across languages plus mcp.rs) green.

(Note: an initial run of criteria 1-3 with `| tail -30` appeared to show
"0 tests" because the truncated tail cut off before reaching tests/mcp.rs
in cargo's per-binary output order; re-running with `grep -A3 "Running
tests/mcp"` confirmed all three tests actually ran and passed.)

## Design requirements (Goal/Steps)

- **Thin wrapper, no duplicated query/note logic**: confirmed. Every tool
  in `src/mcp/mod.rs` (tree, sig, map, deps, refs, at, notes_add, notes,
  notes_list) builds the corresponding `cmd::*::Args` and calls
  `cmd::*::render(&args).0` — no query/note computation lives in
  `src/mcp/`. Verified `cmd::{tree,sig,map,deps,refs,at,notes}.rs` each
  now expose a `pub fn render(&Args) -> (String, ExitCode)` core, with
  `pub fn run(Args) -> ExitCode` reduced to calling `render` and printing
  the result (spot-checked; matches the refactor precedent already
  established in task 09's Decisions section).
- **All required verbs exposed as typed tools**: confirmed — 9
  `#[tool]` methods present: tree, sig, map, deps, refs, at, notes_add,
  notes (show), notes_list.
- **`ctx mcp` starts the server**: confirmed. `cli.rs` has a `Mcp` variant
  (`src/cli.rs:119`, doc comment "Start the MCP server over stdio...");
  `lib.rs:211` dispatches `Some(cli::Command::Mcp) => mcp::serve()`;
  `ctx --help` lists `mcp  Start the MCP server over stdio, exposing the
query and note verbs as typed tools (R15)`.

## Append-only task-file check

`git diff afa2e2b -- specs/codebase-context-tree/tasks/11-mcp-server.md`
shows only an added `<!-- PLAN (build step 1) ... -->` HTML comment block
(the plan-comment block, an allowed addition). No edits to Goal, Steps,
Touch, Budget, or acceptance-criterion text. No Status-line change and no
acceptance checkboxes were ticked in this diff — the task file's
bookkeeping (Status still "in-progress", boxes unchecked, no `## Decisions`
section) was never finalized despite the implementation being complete and
committed (see below). This is a documentation gap, not an acceptance
failure, but is flagged since task 09's equivalent task closed out with a
Status flip, ticked boxes, and a `## Decisions` section documenting the
outside-Touch edits — 11 did not.

## Scope / Touch conformance

Two commits implement this task:

- `b7d3276` refactor: add render cores to `cmd::{at,deps,map,notes,refs,
sig,tree}.rs` — outside the task's declared `Touch:` (which lists only
  `src/mcp/**`, `src/cli.rs`, `Cargo.toml`, `tests/*.rs`).
- `a113d63` feat: MCP server + `Cargo.lock`, `Cargo.toml`, `cli.rs`,
  `lib.rs`, `src/mcp/mod.rs`, `tests/mcp.rs`.

The task's own PLAN comment block pre-declares this exact outside-Touch
edit as "additive wiring per dispatch note; report as Decision," and an
identical pattern (cmd-module wiring + `lib.rs` dispatch arm added outside
a declared `Touch:`) is the accepted, documented convention in task 09's
`## Decisions` section for this same spec. The edits are load-bearing
(the Goal explicitly requires the MCP tools to call the _existing_
cmd::* logic, which structurally requires each cmd module to expose a
stdout-free `render` core) and are a mechanical refactor with no behavior
change (each cmd's own integration tests, which were not modified, still
pass — confirmed via the full `check.sh` run). Flagging per the verification
charter: this is a repo-convention-motivated edit outside the literal
Touch list, and per that convention "the orchestrator widens Touch at
merge" — but no `## Decisions` section was actually added to task 11's
file to record it, unlike task 09's precedent. No other scope creep
(unrelated files, formatting sweeps, version bumps) was found in either
commit.

## Commands run

```
export PATH="$HOME/.cargo/bin:$PATH"
cd context-tree
cargo test mcp_tool_list
cargo test mcp_tree_matches_cli
cargo test mcp_notes_add_writes_file
cd ..
bash context-tree/scripts/check.sh
```
