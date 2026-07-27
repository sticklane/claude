# Porting the toolkit to another runtime

Procedures live once in `.claude/`. Profiles in `runtimes/` map the abstract
tiers onto model selections, headless commands, and native
orchestration. Compatible runtimes consume the shared procedures through
`.agents/skills/` or an installable package, then use the common data layer:
the bd work queue, Codebase-Memory, and the specs under `specs/`.

## Concept map

| Concept | Claude Code | Antigravity | Codex | gemini-cli |
|---|---|---|---|---|
| Skills | `.claude/skills/<name>/SKILL.md`, auto-triggered by description | Discovers the canonical procedures through `.agents/skills/` or the native plugin | Discovers `.claude/skills/` through `.agents/skills/` symlinks or the native plugin | Agent Skills through `gemini skills` |
| Review roles | `.claude/agents/*.md` subagents | Native subagents | Collaboration subagents | Separate `gemini -p` processes |
| Repository context | `CLAUDE.md` + `.claude/rules/` | Root repository instructions | `AGENTS.md` | `GEMINI.md` |
| Headless | `claude -p … --permission-mode dontAsk --max-turns N` | `agy -p … --new-project` | `codex exec … --ephemeral` | `gemini -p … -o json` |
| Orchestration | Workflow tool | Native subagents | Collaboration subagents | Shell fan-out around headless calls |
| Permission modes | `default` / `acceptEdits` / `plan` / `dontAsk` / `bypassPermissions` | Terminal Execution Policy plus command-line mode and sandbox flags | Approval policy plus sandbox mode | `--approval-mode default/auto_edit/plan/yolo` plus Policy Engine |

Each column's authoritative detail lives in its profile:
`runtimes/claude-code.md`, `runtimes/antigravity.md`,
`runtimes/codex.md`, and `runtimes/gemini-cli.md`.

## To add a runtime

1. Write `runtimes/<name>.md` with the four standard sections
   (`## Tiers`, `## Headless`, `## Orchestration`, `## Notes`). Map
   all four tiers, mark the two deep tiers as recommended pin values,
   and record how you verified the headless command syntax.
2. Map each concept in the concept table. Record how the runtime reads bd,
   the code-structure index, and `specs/`, then name its native review and
   orchestration primitives. Expose the canonical skills without copying
   their workflow bodies. Where the runtime has no equivalent, say so
   explicitly in the profile rather than leaving the row blank.
3. Prove the headless plumbing: run `evals/runner-selftest.sh` (shipped
   by task 03 of specs/model-agnostic) with the runtime command-line tool in
   `RUNNER_CMD`. It drives the eval harness through a throwaway
   scenario tree without touching the committed evaluation sets.
