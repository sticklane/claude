# Agentic development toolkit—orientation

This repo IS the toolkit it describes: skills, subagents, and rules for
running an agent-driven spec pipeline, distributed as the `agentic`
plugin. Authoring conventions and always-on rules live in CLAUDE.md and
`.claude/rules/`—this file is the map, not the rulebook.

## Session start

Read `CLAUDE.md` and the applicable `.claude/rules/`, then run `bd prime` for
the tracker workflow. Use `/work` for the attended default; it reads `bd
ready`, claims the selected issue, and closes it after verification. Use
`/drain` only when the user asks to work the ready queue.

## Repo map

- `.claude/`—the source of truth: `skills/` (pipeline stages), `agents/` (scout, critic, verifier...), `rules/` (always-on).
- `.claude-plugin/`, `.codex-plugin/`, `plugin.json`—native Claude Code, Codex, and Antigravity package manifests for plugin `agentic`.
- `skills/`—generated regular-file package entrypoints for Codex and Antigravity; each loads its canonical `.claude/skills/` procedure. Regenerate with `bin/generate-codex-skill-entrypoints --write`; never hand-edit.
- `agentic/`—the `agentic` CLI (Python): fronts bd for tracker workflows and audits Codebase-Memory exploration adoption. `agentic init` bootstraps a clone's tracker from the committed `.beads/issues.jsonl`; `register-spec` creates absent task issues and dependency edges from authored definitions without reading status. `ready`, `resume`, `claim`, `verdict`, and `audit` are live; `shadow-sync` is a hidden non-mutating retirement alias.
- `agentprof/`—pprof profiler for AI-agent token & spend attribution (Claude Code transcripts, GCP billing, OTel; cache re-prime + skill/project attribution metrics—flags and labels in its README/SCHEMA).
- `agent-console/`—local zero-LLM dashboard (workboard view, `/workboard-kanban` board view grouping every repo's spec tasks into status columns, cost panel incl. re-prime line) for this machine's Claude Code setup.
- `.claude/skills/codebase-memory/`—the code-exploration contract: use the
  bundled Codebase-Memory MCP server for structure first; if unavailable,
  use bounded `rg` plus small reads without claiming graph coverage.
- `antigravity/`, `codex/`—runtime install and native-execution guides. The 2026-07-22 portability pivot removed the former copied procedure trees.
- `bin/`—installer scripts (quality gates, skill sync).
- `docs/`—research and doctrine (anthropic-playbook, external-playbooks, memory index).
- `evals/`—skill eval scenarios plus the headless runner.
- `hooks/`—hooks this repo ships. **Only two are wired here as of 2026-07-29**: post-tool-format (PostToolUse, in `.claude/settings.json`) and session-refresh (UserPromptSubmit, per-user in `~/.claude/settings.json`). Everything else—plugin-staleness, plugin-autorefresh, bd-compliance, bd-bootstrap, handoff-resume, and the review-gate git `pre-commit` hook—ships for consuming repos but is deliberately unwired here: nine accreted hooks fired unpredictably, three warned about conditions they could have fixed, and the Stop gate re-ran a 5m10s suite over unchanged trees. Consuming repos still install the gate via `bin/install-gates`; `bin/install-review-gate` still installs the commit gate per repository. Re-wiring any of them here is a deliberate decision, not a default.
- `runtimes/`—per-runtime profiles mapping tier language to concrete models.
- `specs/`—one directory per spec with `SPEC.md` and `tasks/`; `specs/QUEUE.md` is the combined wave plan.
- `templates/`—hook and check-script templates the installers copy from.
- `tests/`—shell tests for the installers and hook templates.

## State

- **bd (beads) is the canonical live state** for task status, dependencies, and ready-work (agentic-core-redesign cutover). Task-file `Status:` headers in `specs/*/tasks/*.md` are frozen display: no live procedure scans or updates them. `agentic register-spec` reads authored definitions once to create absent issues and edges.
- `specs/QUEUE.md` is the wave plan—dispatch order, not live state.
- Registered-definition immutability preserves each task's provenance; it does not freeze the workset forever. If genuinely new mandatory scope appears after registration, re-read the live bd graph, author a new immutable dependent task, add it and its edges through the guarded coordinator, and expose it only in a later freshly sealed wave. Never rewrite a registered task file or live acceptance/notes to smuggle new scope to a pointer-only worker. If the requirement was already part of an existing definition, repair that existing owner instead of inventing an extension.
- `./specs/status.sh` renders the live dashboard from bd on demand (`bd ready` + `bd list`).
- In-flight session handoffs land in bd, not on disk: `/handoff` opens one `handoff`-labeled issue per parked session, linked by a `tracks` dependency to every issue it leaves open. `bd list --label handoff --status=open` is the discovery surface the resume hook and `/resume-handoff` both read; `/resume-handoff` closes that issue once the work is picked back up.

`/work` is the attended daily default: it answers "what's next" by running
`bd ready` and works the picked issue, claiming it in bd before starting and
closing it in bd when done. Unattended queue mode is the same skill run
headless.

## Commands

All re-verified 2026-07-11 (each run green); run from the repo root.

- `bash scripts/check.sh`—the canonical check: runs every `tests/test_*.sh` plus the `tests/test_agentic_*.py` pytest suite (both by glob), with two other-spec-owned tests quarantined known-red.
- `./specs/status.sh`—renders the live dashboard from bd; prints one row per issue and a TOTAL of the ready count plus each non-ready bd status.
- `bash tests/test_status_cutover.sh`—proves `status.sh`'s totals equal bd's counts (`CUTOVER OK`).
- `claude plugin validate .`—proves the plugin + marketplace manifests are valid.
- `python3 ~/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py .`—validates the Codex plugin package; `agy plugin validate .` validates the Antigravity package and reports the discovered skill count.
- `bash tests/test_codex_skill_entrypoints.sh`—proves all shared runtime entrypoints are present, generated wrappers are current, and shared skill instructions contain no executable cross-runtime Claude CLI recipes.
- `for t in tests/test_*.sh; do bash "$t"; done`—proves installers and hook templates work.
- `./bin/check-agent-model-pins`—proves every `.claude/agents/*.md` pins a model alias in {haiku, sonnet, opus}.
- `./evals/runner-selftest.sh`—proves the eval runner's plumbing (stub CLI, no model calls); full skill evals run via `./evals/run.sh <skill>` (headless model sessions—spend).
- `bash agentprof/scripts/check.sh`—proves agentprof's Go build: gofmt, vet, tests.
- `agentprof census`—count skill activations (and, with `--kind all`, tool calls) across Claude Code, Codex, and Antigravity for one window.
- `bash agent-console/scripts/check.sh`—proves agent-console's py_compile, render smoke test, and unit tests.
- `bash tests/test_codebase_memory_integration.sh`—proves the pinned installer,
  launcher isolation, MCP packaging, routing doctrine, and skill contract.

<!-- BEGIN BEADS INTEGRATION v:1 profile:minimal hash:970c3bf2 -->

## Beads Issue Tracker

This project uses **bd (beads)** for issue tracking. Run `bd prime` to see full workflow context and commands.

### Quick Reference

```bash
bd ready              # Find available work
bd show <id>          # View issue details
bd update <id> --claim  # Claim work
bd close <id>         # Complete work
```

### Rules

- Use `bd` for ALL task tracking — do NOT use TodoWrite, TaskCreate, or markdown TODO lists (see the task-tool stance below).
- Run `bd prime` for detailed command reference and session close protocol
- Use `bd remember` for persistent knowledge — do NOT use MEMORY.md files

The repository intentionally forbids the harness-native task tools:
`TaskCreate`, `TaskUpdate`, and `TaskList` are not used. They are session-scoped
and cannot provide durable dependency edges, cross-session provenance, or
inter-session resume that `bd` provides. The recurring harness suggestion
“consider using TaskCreate” is therefore known surface friction and an accepted
documentation debt; this repo keeps the `bd` preference as the canonical rule.

**Architecture in one line:** issues live in a local Dolt DB; sync uses `refs/dolt/data` on your git remote; `.beads/issues.jsonl` is a passive export. See https://github.com/gastownhall/beads/blob/main/docs/SYNC_CONCEPTS.md for details and anti-patterns.

## Agent Context Profiles

The managed Beads block is task-tracking guidance, not permission to override repository, user, or orchestrator instructions.

- **Conservative (default)**: Use `bd` for task tracking. Do not run git commits, git pushes, or Dolt remote sync unless explicitly asked. At handoff, report changed files, validation, and suggested next commands.
- **Minimal**: Keep tool instruction files as pointers to `bd prime`; use the same conservative git policy unless active instructions say otherwise.
- **Team-maintainer**: Only when the repository explicitly opts in, agents may close beads, run quality gates, commit, and push as part of session close. A current "do not commit" or "do not push" instruction still wins.

## Session Completion

This protocol applies when ending a Beads implementation workflow. It is subordinate to explicit user, repository, and orchestrator instructions.

1. **File issues for remaining work** - Create beads for anything that needs follow-up
2. **Run quality gates** (if code changed) - Tests, linters, builds
3. **Update issue status** - Close finished work, update in-progress items
4. **Handle git/sync by active profile**:

   ```bash
   # Conservative/minimal/default: report status and proposed commands; wait for approval.
   git status

   # Team-maintainer opt-in only, unless current instructions forbid it:
   git pull --rebase
   bd dolt push
   git push
   git status
   ```

5. **Hand off** - Summarize changes, validation, issue status, and any blocked sync/commit/push step

**Critical rules:**

- Explicit user or orchestrator instructions override this Beads block.
- Do not commit or push without clear authority from the active profile or the current user request.
- If a required sync or push is blocked, stop and report the exact command and error.
<!-- END BEADS INTEGRATION -->

Cutover complete (2026-07-22, core task 09, specs/agentic-core-redesign):
**bd is now the source of truth** for spec-task state, dependencies, and
ready-work. The markdown task headers under `specs/` are frozen display;
`specs/status.sh` and the work loop read bd, not the headers. The Beads
block above (including its "do not use markdown TODO lists" rule) is fully
in force.
