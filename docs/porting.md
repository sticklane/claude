# Porting the toolkit to another runtime

The toolkit's core speaks abstract tiers and defers runtime specifics
to profiles in `runtimes/` (selection convention:
`runtimes/README.md`). This guide maps each toolkit concept onto the
runtimes we know about, and ends with a checklist for adding a new one.

## Concept map

| Concept | Claude Code | Antigravity (reference port: `antigravity/`) | gemini-cli |
|---|---|---|---|
| Skills | `.claude/skills/<name>/SKILL.md`, auto-trigger by description | `.agents/skills/`, same auto-trigger (see `antigravity/README.md`) | agent skills via `gemini skills` |
| Agents (scout/critic/verifier) | `.claude/agents/*.md` subagents | skills with the same names, run in a fresh Agent Manager conversation | no subagent primitive — separate `gemini -p` processes |
| Rules (always-on) | `CLAUDE.md` + `.claude/rules/` | `AGENTS.md` (always-on by definition) | `GEMINI.md` context file |
| Hooks | `.claude/settings.json` hooks | `.agents/hooks.json` (different JSON shape) | `gemini hooks` |
| Headless | `claude -p … --permission-mode dontAsk --max-turns N` | none — Agent Manager launches instead | `gemini -p … -o json` (no turn-cap flag; `maxSessionTurns` in settings) |
| Orchestration (workflows / fan-out) | Workflow tool; scripts in `.claude/workflows/` behind the human "ultracode" opt-in | none scripted — sequential markdown workflows + human-dispatched Agent Manager parallelism | none native — shell fan-out around headless calls with JSON output |
| Permission modes | `default` / `acceptEdits` / `plan` / `dontAsk` / `bypassPermissions` | Terminal Execution Policy (Off/Auto/Turbo) + deny list, Settings UI | `--approval-mode default/auto_edit/plan/yolo` + Policy Engine |

Each column's authoritative detail lives in its profile:
`runtimes/claude-code.md`, `runtimes/antigravity.md`,
`runtimes/gemini-cli.md`.

## To add a runtime

1. Write `runtimes/<name>.md` with the four standard sections
   (`## Tiers`, `## Headless`, `## Orchestration`, `## Notes`) — map
   all four tiers, mark the two deep tiers as recommended pin values,
   and record how you verified the headless command syntax.
2. Port or map each concept in the table above (skills, agents, rules,
   hooks, headless, orchestration, permission modes). Where the runtime
   has no equivalent, say so explicitly in the profile rather than
   leaving the row blank.
3. Prove the headless plumbing: run `evals/runner-selftest.sh` (shipped
   by task 03 of specs/model-agnostic) with the runtime's CLI in
   `RUNNER_CMD` — it drives the eval harness through a throwaway
   scenario tree without touching the committed evalsets.
