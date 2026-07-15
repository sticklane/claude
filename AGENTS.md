# Agentic development toolkit—orientation

This repo IS the toolkit it describes: skills, subagents, and rules for
running an agent-driven spec pipeline, distributed as the `agentic`
plugin. Authoring conventions and always-on rules live in CLAUDE.md and
`.claude/rules/`—this file is the map, not the rulebook.

## Repo map

- `.claude/`—the source of truth: `skills/` (pipeline stages), `agents/` (scout, critic, verifier...), `rules/` (always-on).
- `.claude-plugin/`—plugin + marketplace manifests distributing the toolkit as plugin `agentic`.
- `agentprof/`—pprof profiler for AI-agent token & spend attribution (Claude Code transcripts, GCP billing, OTel; cache re-prime + skill/project attribution metrics—flags and labels in its README/SCHEMA).
- `agent-console/`—local zero-LLM dashboard (workboard view, cost panel incl. re-prime line) for this machine's Claude Code setup.
- `antigravity/`—mirrored port of `.claude/` for the Antigravity runtime.
- `codex/`—thin overlay on `antigravity/` for the Codex runtime: symlinked skills plus three real-content wrappers (drain/build/evals); port chain is `.claude/` → `antigravity/` → `codex/` (CLAUDE.md's port-chain bullet).
- `bin/`—installer scripts (quality gates, skill sync).
- `docs/`—research and doctrine (anthropic-playbook, external-playbooks, memory index).
- `evals/`—skill eval scenarios plus the headless runner.
- `runtimes/`—per-runtime profiles mapping tier language to concrete models.
- `specs/`—one directory per spec with `SPEC.md` and `tasks/`; `specs/QUEUE.md` is the combined wave plan.
- `templates/`—hook and check-script templates the installers copy from.
- `tests/`—shell tests for the installers and hook templates.

## State

- Task-file `Status:` headers (in `specs/*/tasks/*.md`) are the canonical live state.
- `specs/QUEUE.md` is the wave plan—dispatch order, not live state.
- `./specs/status.sh` renders the live dashboard from the headers on demand.
- In-flight session handoffs land as `HANDOFF.md` next to the active task/spec file (or `.claude/HANDOFF.md`).

## Commands

All re-verified 2026-07-11 (each run green); run from the repo root.

- `./specs/status.sh`—proves the queue parses; prints per-task status rows and totals.
- `claude plugin validate .`—proves the plugin + marketplace manifests are valid.
- `for t in tests/test_*.sh; do bash "$t"; done`—proves installers and hook templates work.
- `./bin/check-agent-model-pins`—proves every `.claude/agents/*.md` pins a model alias in {haiku, sonnet, opus}.
- `./evals/runner-selftest.sh`—proves the eval runner's plumbing (stub CLI, no model calls); full skill evals run via `./evals/run.sh <skill>` (headless model sessions—spend).
- `bash agentprof/scripts/check.sh`—proves agentprof's Go build: gofmt, vet, tests.
- `bash agent-console/scripts/check.sh`—proves agent-console's py_compile, render smoke test, and unit tests.
