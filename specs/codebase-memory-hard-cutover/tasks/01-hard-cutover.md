# Task 01: Replace ctx with Codebase-Memory

Status: pending
Depends on: none
Priority: P0
Budget: 50 turns
Spec: ../SPEC.md (requirements R1–R7)
Touch: config/**, bin/**, .mcp.json, .codex-mcp.json, .claude-plugin/plugin.json, .codex-plugin/plugin.json, .claude/skills/**, skills/**, .claude/rules/**, .claude/agents/**, agentic/**, agentprof/**, docs/**, evals/**, tests/**, context-tree/**, .context/**, specs/**, AGENTS.md, CLAUDE.md, README.md, codex/README.md, antigravity/README.md, runtimes/**

## Goal

The toolkit uses checksum-pinned Codebase-Memory as its sole code-exploration
backend. Installation, launch isolation, Claude/Codex MCP packaging, runtime
doctrine, telemetry, and tests are current, and every path in the exact ctx
retirement manifest is gone from the tracked working tree.

This is one atomic task because the maintainer explicitly rejected a staged
cutover. No intermediate state with both backends, or with neither backend,
is a shippable unit.

## Touch

The broad paths reflect an intentional repository-wide retirement. Preserve
all unrelated dirty hunks in retained files. Read every dirty retained-file
diff before editing, and stop on a conflicting or foreign-owned hunk.

## Steps

1. Record the base revision, worktree/session inventory, and dirty targeted
   paths. Read the two dirty retirement diffs before deleting them.
2. Write the failing network-free installer, launcher, MCP packaging, routing,
   telemetry, and retirement tests first. Run them and confirm failures name
   the missing Codebase-Memory surface.
3. Add the release pin, atomic installer, fail-closed launcher, and
   schema-specific Claude/Codex MCP declarations.
4. Replace the canonical skill and all retained routing surfaces, regenerate
   portable skill entrypoints, and replace ctx eval scenarios.
5. Migrate `agentprof` usage/schema labels and `agentic audit`.
6. Create the exact routing and retirement manifests, then remove every
   retirement target and rewrite all incoming retained references.
7. Run the network-free gates, plugin validators, and the supported-host live
   CBM smoke. Record the live smoke in `../evidence/live-smoke.md`.

## Acceptance

- [ ] `bash tests/test_codebase_memory_integration.sh` → all installer,
  launcher, MCP packaging, routing, and skill-contract fixtures pass.
- [ ] `bash tests/test_no_ctx_surface.sh` → all retirement paths are absent
  and no non-allowlisted ctx product references remain.
- [ ] `bash tests/test_codebase_memory_live.sh` → the pinned archive is
  verified and four real CBM queries pass in temporary roots.
- [ ] `bash agentprof/scripts/check.sh` → Go format, vet, and tests pass with
  Codebase-Memory telemetry names.
- [ ] `python3 -m pytest -q tests/test_agentic_audit.py
  tests/test_agentic_cli_retirement.py` → audit and CLI tests pass.
- [ ] `bash tests/test_codex_skill_entrypoints.sh` → generated skill
  entrypoints are current.
- [ ] `python3 ~/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py
  .` → Codex plugin validation passes.
- [ ] `claude plugin validate .` → Claude plugin validation passes.
- [ ] `agy plugin validate .` → Antigravity plugin validation passes.
- [ ] `bash scripts/check.sh` → canonical repository gate passes.

