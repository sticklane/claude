# Using this toolkit with Google Antigravity

Antigravity runs the same workflow skills as Claude Code and Codex. The
procedures have one source in [`.claude/skills/`](../.claude/skills/);
repository sessions discover them through [`.agents/skills/`](../.agents/skills/),
and the installable Antigravity plugin exposes generated entrypoints under
[`skills/`](../skills/). Those entrypoints load the canonical procedure
instead of copying it.

## Install

For this checkout, no global install is required. Start `agy` from the
repository root and Antigravity discovers `.agents/skills/`.

To make the workflows available in every Antigravity workspace, clone the
toolkit and install its local plugin:

```bash
git clone https://github.com/sticklane/claude.git ~/agentic-toolkit
agy plugin validate ~/agentic-toolkit
agy plugin install ~/agentic-toolkit
agy plugin list
```

The plugin stages all 29 skills, including `evals`. Running `evals` still
requires an explicit user invocation because it starts paid headless
sessions; it is an installed workflow, not a developer-only repo command.

## Native execution

Antigravity consumes the common bd queue, Codebase-Memory graph, and `specs/`
artifacts, but it executes orchestration with Antigravity primitives:

- `invoke_subagent` and `define_subagent` for attended fan-out and
  verification.
- `Workspace: 'branch'` for isolated writers; shared-workspace writers run
  serially.
- `agy -p --new-project` for Antigravity headless sessions and skill evals.

A shared skill may describe the Claude Code and Codex adapters, but an
Antigravity run never launches either runtime. The
[`antigravity` runtime profile](../runtimes/antigravity.md) owns its model,
headless, permission, and orchestration mappings.

`gate` selects the Antigravity lifecycle adapter explicitly. It writes
`.agents/hooks.json` and `.agents/hooks/*.sh`, alongside the shared
`scripts/check.sh` and git pre-commit gate. Its hooks use Antigravity's
camelCase payloads and native `deny`/`continue` decisions.

## Shared state

- **Ready work:** `bd ready --json` and `bd show <id>`.
- **Code structure:** Codebase-Memory through the toolkit launcher. Query it
  first; when unavailable, use bounded `rg` plus small reads and report that
  graph coverage was not checked.
- **Definitions and evidence:** `specs/<slug>/SPEC.md`, task files, and
  evidence directories. Live status and dependencies remain in bd.

The old copied Antigravity procedure tree was retired because it drifted.
The current layout keeps one procedure source while retaining a native
Antigravity execution adapter.

## Antigravity registration

Antigravity's plugin manifest has no bundled-MCP field. Add a stdio server
named `codebase-memory-mcp` with command
`agentic-codebase-memory-mcp` through Antigravity's native `/mcp` manager or
in `~/.gemini/config/mcp_config.json`. Do not substitute a Claude Code or
Codex registration command.
