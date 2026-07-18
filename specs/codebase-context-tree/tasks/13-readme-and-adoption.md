# Task 13: README, adoption snippet, MCP registration docs

Status: done
Depends on: 11, 12
Priority: P2
Budget: 25 turns
Spec: ../SPEC.md (requirement R17)
Touch: context-tree/README.md

## Goal

`context-tree/README.md` documents install, `ctx init`, the full query and
note command surface, the note file format, and the documented check
command (`bash context-tree/scripts/check.sh`, established in task 01)
that runs the component's full test suite. It carries the v1 adoption
story (CUJS.md CUJ0): a copy-paste integration snippet for a consuming
repo's CLAUDE.md/AGENTS.md routing structure questions to `ctx` before
file reads or scout dispatch, delimited by the literal marker
`ctx-integration-snippet` (open and close), plus MCP registration
instructions for the server built in task 11.

## Steps

1. Write the README covering: install/build, `ctx init`, each query
   command (tree/sig/map/deps/refs/at) with example invocations and
   sample output, the note commands (`ctx notes add`/`ctx notes`/`ctx
notes list`) and note file format, `ctx hooks install`/`uninstall`,
   and the documented check command.
2. Add the adoption snippet: a fenced block a consuming repo can paste
   into its CLAUDE.md/AGENTS.md, wrapped in two literal marker lines
   containing `ctx-integration-snippet` (open and close) so both an
   installer script and this acceptance criterion can locate it
   mechanically.
3. Add MCP registration instructions (how to point an MCP-capable client
   at the `ctx mcp` stdio server from task 11).
4. Load `/prose-review`'s doctrine before finalizing prose (README.md is
   human-facing per this repo's CLAUDE.md convention) and self-review
   against it: Diátaxis structure, Google style essentials, no AI
   antipatterns.

## Acceptance

- [x] `test -f context-tree/README.md` → exists
      (evidence: command exits 0, README committed at 36f364e)
- [x] `grep -c "ctx-integration-snippet" context-tree/README.md` → ≥ 2
      (open and close markers) (evidence: returns 2 — the `:start`/`:end` marker comments)
- [x] `grep -qi "mcp" context-tree/README.md && grep -qi "registration\|register" context-tree/README.md` →
      both match (MCP registration instructions present)
      (evidence: both greps exit 0 — "## MCP registration" section documents `ctx mcp` + `claude mcp add`/`.mcp.json`)
- [x] `grep -q "context-tree/scripts/check.sh" context-tree/README.md` →
      matches (documented check command named)
      (evidence: grep exits 0 — named in "## Running the checks")
