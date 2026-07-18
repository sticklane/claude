# context-tree (`ctx`)

`ctx` answers structure questions about a codebase — the shape of a file,
a symbol's signature, what imports what, where a symbol is used — from a
local index instead of from raw file reads. An agent that routes those
questions through `ctx` spends a fraction of the tokens a file read or a
scout dispatch would cost, and a human gets the same answers without
opening an editor.

It indexes 11 languages through tree-sitter (C, C++, Bash, Go, Haskell,
Java, JavaScript/TypeScript, Kotlin, OCaml, Python, Rust, Zig), keeps the
index in a local SQLite database, and re-syncs on demand before each query.

## Install

`ctx` builds from source with a stable Rust toolchain and Cargo.

```sh
cargo build --release
```

The binary lands at `target/release/ctx`. Put it on your `PATH`, or invoke
it by its full path. The rest of this document writes `ctx`.

## Initialize a project

Run `ctx init` once at the root of a project. It scaffolds a `.context/`
directory (at the VCS root when the project is under version control) that
holds the index and the note store:

```sh
$ ctx init
initialized .context/ at /path/to/project
```

Without a VCS, `ctx init` scaffolds `.context/` in the current directory.
`ctx init` is idempotent — running it again on an initialized root changes
nothing and exits 0. Every query command re-syncs the index from the
current source before it answers, so you never run a separate "reindex"
step. Pass `--no-sync` to skip that sync and query the last-built index.

## Query commands

Each query prints plain text by default and structured JSON with `--json`,
so an agent can parse the result and a human can read it. Symbol arguments
resolve by suffix: pass the shortest unambiguous tail of a symbol's path
(`parse_note`, or `notes.mod.parse_note` to disambiguate). An ambiguous
symbol prints its candidates instead of guessing.

### `ctx tree <path>` — outline a file or directory

Lists the symbols a file or directory contains, nested by scope.

```sh
$ ctx tree context-tree/src/notes
context-tree/src/notes/anchor.rs
  enum Resolution
  function resolve
context-tree/src/notes/mod.rs
  struct Note
  function parse_note
  function write_note
```

Options: `--depth <N>` limits nesting depth, `--limit <N>` caps the number
of entries (default 200), `--doc` includes docstrings.

### `ctx sig <symbol>` — signature and docstring

Prints a symbol's signature and, on the following lines, its docstring.

```sh
$ ctx sig parse_note
pub fn parse_note(rel_path: &str, text: &str) -> Result<Note, String>
Parse a note's YAML frontmatter and body. Returns `Err(reason)` [...]
```

Options: `--doc` prints the full docstring rather than the first line.

### `ctx map` — ranked project overview

Ranks the codebase's symbols by reference-graph importance and prints the
most important ones up to a token budget — a fast orientation for an
unfamiliar repo.

```sh
$ ctx map --tokens 400
```

Options: `--tokens <N>` sets the output budget (default 1000), `--doc`
includes docstrings.

### `ctx deps <path>` — import edges

Prints the module-level imports out of a path.

```sh
$ ctx deps context-tree/src/notes/mod.rs
context-tree.src.notes.mod -> crate::project::CONTEXT_DIR
context-tree.src.notes.mod -> sha2::sha2
context-tree.src.notes.mod -> std::fs
```

Options: `--reverse` prints the importers of the path instead.

### `ctx refs <symbol>` — definitions and references

Lists where a symbol is defined and where it is referenced.

```sh
$ ctx refs parse_note --limit 6
def context-tree.src.notes.mod.parse_note context-tree/src/notes/mod.rs:46
ref parse_note context-tree/src/notes/mod.rs:108
ref parse_note context-tree/src/notes/mod.rs:255
```

Options: `--limit <N>` caps the number of references (default 50).

### `ctx at <file>:<line>` — enclosing symbol

Prints the innermost symbol enclosing a line (1-based) and its containment
chain — the answer to "what am I looking at?".

```sh
$ ctx at context-tree/src/notes/mod.rs:60
module context-tree.src.notes.mod
  function context-tree.src.notes.mod.parse_note — pub fn parse_note[...]
```

## Notes

Notes anchor a piece of prose — a gotcha, an invariant, a rationale, a
TODO — to a symbol, so the knowledge travels with the code rather than
decaying in a wiki. A note stays _fresh_ while its anchor still resolves
and the anchored code is unchanged, and reads as _stale_ once either
diverges.

### `ctx notes add <symbol> [text]` — anchor a note

```sh
$ ctx notes add parse_note "Frontmatter must be valid YAML." --kind gotcha
note added: .context/notes/01KXSMBY4VHFKE0FCJS6YKR2GC.md -> [...].parse_note
```

The body comes from the positional `text`, from `--file <path>`, or from
stdin (`--file -`). Options: `--kind <kind>` classifies the note as
`gotcha`, `invariant`, `rationale`, or `todo`.

### `ctx notes <symbol>` — show a symbol's notes

```sh
$ ctx notes parse_note
01KXSMBY4VHFKE0FCJS6YKR2GC  fresh  kind=gotcha
Frontmatter must be valid YAML.
```

### `ctx notes list` — list and filter notes

Lists every note. Options: `--kind <kind>` filters by classification,
`--stale` shows only stale notes, `--file <path>` shows only notes
anchored in a file.

### Note file format

Each note is a single Markdown file under `.context/notes/`, named by a
ULID, with a YAML frontmatter header:

```markdown
---
id: 01KXSMBY4VHFKE0FCJS6YKR2GC
anchor_path: context-tree.src.notes.mod.parse_note
anchor_hash: f48c9c8112a30740b51a8c4401d4b5a9af7166203b53929c7baaca28ff3dd792
kind: gotcha
author: you@example.com
created: 2026-07-18T03:29:53Z
---

Frontmatter must be valid YAML.
```

`id`, `anchor_path`, and `anchor_hash` are required; `kind`, `author`, and
`created` are optional and filled in for you at creation. Notes are plain
tracked files — review, edit, and delete them in a normal pull request,
like any other source.

## Git hooks

`ctx hooks install` wires `ctx` into a repository: it installs a pre-warm
hook and a pre-commit hook that keeps note anchors current, and prints a
`PostToolUse` snippet for agent harnesses. Under git it also enables the
built-in filesystem monitor when the installed git version supports it,
reporting whether it did.

```sh
$ ctx hooks install
```

`ctx hooks uninstall` removes exactly the block `ctx` added and reverts
only the settings `ctx` itself set.

## MCP registration

`ctx mcp` runs an [MCP](https://modelcontextprotocol.io) server over stdio
that exposes the query and note commands as typed tools (`tree`, `sig`,
`map`, `deps`, `refs`, `at`, `notes`, `notes_add`, `notes_list`). Register
it with any MCP-capable client to give an agent the tools directly.

For Claude Code, register the server from the project root:

```sh
claude mcp add ctx -- /absolute/path/to/ctx mcp
```

Or add it to the project's `.mcp.json` by hand:

```json
{
  "mcpServers": {
    "ctx": {
      "command": "/absolute/path/to/ctx",
      "args": ["mcp"]
    }
  }
}
```

Registering the server loads its tool schemas (~1–2k tokens) into every
session, whether the agent uses them or not. For a token-sensitive
harness, the CLI path through a shell is the cheaper door — the same
answers, loaded only when a command runs. Use whichever fits the client.

## Adoption: route structure questions to `ctx`

To put `ctx` in an agent's hands, paste the block below into a consuming
repo's `CLAUDE.md` or `AGENTS.md`. It tells the agent to reach for `ctx`
before reading files or dispatching a scout to answer a structure
question. The marker comments delimit the block so an installer script can
find and update it; leave them in place.

<!-- ctx-integration-snippet:start -->

## Answering structure questions

Before you read a file or dispatch a scout to answer a "where is / what
calls / what's the shape of" question, ask `ctx` — it reads the index, not
the raw files, so it answers in a fraction of the tokens:

- What does this file or module contain? → `ctx tree <path>`
- What's this symbol's signature and doc? → `ctx sig <symbol>`
- What are the important symbols here? → `ctx map`
- What does this import, or what imports it? → `ctx deps <path>` (add `--reverse`)
- Where is this symbol defined and used? → `ctx refs <symbol>`
- What encloses this `file:line`? → `ctx at <file>:<line>`
- Are there pinned gotchas on this symbol? → `ctx notes <symbol>`

Fall back to reading the file or dispatching a scout only when `ctx` can't
answer — the symbol isn't indexed, or you need the full body.
<!-- ctx-integration-snippet:end -->

## Running the checks

`bash context-tree/scripts/check.sh` runs the component's full check
suite — format check, Clippy with warnings denied, and the test suite:

```sh
$ bash context-tree/scripts/check.sh
```

Run it green before you call a change to `context-tree` done.
