# Agentic development toolkit—orientation

This repo IS the toolkit it describes: skills, subagents, and rules for
running an agent-driven spec pipeline, distributed as the `agentic`
plugin. Authoring conventions and always-on rules live in CLAUDE.md and
`.claude/rules/`—this file is the map, not the rulebook.

## Repo map

- `.claude/`—the source of truth: `skills/` (pipeline stages), `agents/` (scout, critic, verifier...), `rules/` (always-on).
- `.claude-plugin/`—plugin + marketplace manifests distributing the toolkit as plugin `agentic`.
- `agentic/`—the `agentic` CLI (Python): fronts bd (tracker) and ctx (index) behind one command. `agentic init` bootstraps a clone's tracker from the committed `.beads/issues.jsonl`; `ready`, `resume`, `claim`, `verdict`, `audit`, and `shadow-sync` (mirror `specs/*/tasks/*.md` headers into bd) are live; the rest are stubs.
- `agentprof/`—pprof profiler for AI-agent token & spend attribution (Claude Code transcripts, GCP billing, OTel; cache re-prime + skill/project attribution metrics—flags and labels in its README/SCHEMA).
- `agent-console/`—local zero-LLM dashboard (workboard view, `/workboard-kanban` board view grouping every repo's spec tasks into status columns, cost panel incl. re-prime line) for this machine's Claude Code setup.
- `context-tree/`—Rust CLI `ctx` + MCP server: tree-sitter symbol index (12 languages), structural queries (tree/sig/map/deps/refs/at), refactor-surviving symbol notes; the `/ctx` skill teaches agents to use it.
- `antigravity/`, `codex/`—one-page READMEs pointing at the data layer (bd's queue, ctx's index, `specs/`); the former mirrored-port trees were deleted in the 2026-07-22 portability pivot (CLAUDE.md's "Authoring conventions").
- `bin/`—installer scripts (quality gates, skill sync).
- `docs/`—research and doctrine (anthropic-playbook, external-playbooks, memory index).
- `evals/`—skill eval scenarios plus the headless runner.
- `hooks/`—this repo's own Claude Code hooks, wired in `.claude/settings.json`: plugin-staleness (SessionStart warn), plugin-autorefresh (Stop auto-update after a pushed version bump), handoff-resume, session-refresh; bd-bootstrap ships here too (SessionStart, opt-in — not yet wired; see its README).
- `runtimes/`—per-runtime profiles mapping tier language to concrete models.
- `specs/`—one directory per spec with `SPEC.md` and `tasks/`; `specs/QUEUE.md` is the combined wave plan.
- `templates/`—hook and check-script templates the installers copy from.
- `tests/`—shell tests for the installers and hook templates.

## State

- **bd (beads) is the canonical live state** for task status, dependencies, and ready-work (agentic-core-redesign cutover). Task-file `Status:` headers in `specs/*/tasks/*.md` are frozen display, no longer scanned.
- `specs/QUEUE.md` is the wave plan—dispatch order, not live state.
- `./specs/status.sh` renders the live dashboard from bd on demand (`bd ready` + `bd list`).
- In-flight session handoffs land as `HANDOFF.md` next to the active task/spec file (or `.claude/HANDOFF.md`; `HANDOFF-<topic>.md` when that slot is occupied — the resume hook matches `HANDOFF*.md`), each carrying a `Tracked:` header naming the bd issue(s) for the parked work.

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
- `for t in tests/test_*.sh; do bash "$t"; done`—proves installers and hook templates work.
- `./bin/check-agent-model-pins`—proves every `.claude/agents/*.md` pins a model alias in {haiku, sonnet, opus}.
- `./evals/runner-selftest.sh`—proves the eval runner's plumbing (stub CLI, no model calls); full skill evals run via `./evals/run.sh <skill>` (headless model sessions—spend).
- `bash agentprof/scripts/check.sh`—proves agentprof's Go build: gofmt, vet, tests.
- `bash agent-console/scripts/check.sh`—proves agent-console's py_compile, render smoke test, and unit tests.
- `bash context-tree/scripts/check.sh`—proves context-tree's Rust build: fmt, clippy, tests (needs the Rust toolchain).

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

- Use `bd` for ALL task tracking — do NOT use TodoWrite, TaskCreate, or markdown TODO lists
- Run `bd prime` for detailed command reference and session close protocol
- Use `bd remember` for persistent knowledge — do NOT use MEMORY.md files

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
