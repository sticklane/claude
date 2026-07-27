# Using this toolkit with OpenAI Codex

Codex runs the same workflow skills as Claude Code and Antigravity. The
procedures have one source in [`.claude/skills/`](../.claude/skills/).
Repository sessions discover that source through
[`.agents/skills/`](../.agents/skills/). Installed Codex plugins use the
regular-file entrypoints under [`skills/`](../skills/), because the Codex
plugin cache does not preserve symlinked skill directories; each generated
entrypoint loads the canonical procedure instead of copying it.

## Install

For this checkout, no plugin install is required. Start Codex from the
repository root and it discovers `.agents/skills/`.

To install the plugin globally from a clone:

```bash
codex plugin marketplace add ~/agentic-toolkit
codex plugin add agentic@agentic-toolkit
codex plugin list
```

The package exposes all 29 skills, including `evals`, and includes the eval
runner and scenarios. `evals` has Codex's native
`allow_implicit_invocation: false` policy because every run starts paid
headless sessions; users can still invoke it explicitly.

## Native execution

Codex uses its collaboration primitives for workflow orchestration:

- `spawn_agent`, `wait_agent`, and `followup_task` for attended fan-out.
- Parallel read-only panels and serialized writers unless isolated
  worktrees are available.
- `codex exec` for Codex headless sessions and skill evals.

A shared skill may describe the Claude Code and Antigravity adapters, but a
Codex run never launches either runtime. The
[`codex` runtime profile](../runtimes/codex.md) owns its model, headless,
permission, and orchestration mappings.

`gate` selects the Codex lifecycle adapter explicitly. It writes
`.codex/hooks.json` and `.codex/hooks/*.sh`, alongside the shared
`scripts/check.sh` and git pre-commit gate. Review and trust new project hooks
through Codex's `/hooks` view before relying on them.

## Shared state

- **Ready work:** `bd ready --json` and `bd show <id>`.
- **Code structure:** `.codex-plugin/plugin.json` registers
  `codebase-memory-mcp` inline through `agentic-codebase-memory-mcp`. Query
  Codebase-Memory first; when unavailable, use bounded `rg` plus small reads
  and report that graph coverage was not checked.
- **Definitions and evidence:** `specs/<slug>/SPEC.md`, task files, and
  evidence directories. Live status and dependencies remain in bd.

The repository gate checks source-to-entrypoint coverage, generated wrapper
freshness, native package manifests, and the ban on executable Claude
command-line recipes inside shared skills.
