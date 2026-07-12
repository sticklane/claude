# Runtime profile: antigravity

Describes how the abstract tiers and surfaces map onto Antigravity. The
`antigravity/` directory in this repo is the reference port (skills,
workflows, AGENTS.md, hooks); this profile describes it, it does not
replace it.

"Antigravity" always means the `antigravity` CLI (confirmed installed
locally at `~/.antigravity/antigravity/bin/antigravity`, v1.107.0) plus the
Agent Manager GUI it opens — never the GUI alone. The CLI ships a `chat`
subcommand; see `## Headless` below for exactly what that does and does
not enable.

## Tiers

| Tier          | Model                                             | Notes                                                                                         |
| ------------- | ------------------------------------------------- | --------------------------------------------------------------------------------------------- |
| scout-tier    | Flash-class model                                 | The port's own vocabulary (`antigravity/README.md`): "pick a Flash-class model for scouting". |
| session-tier  | the session model                                 | Whatever model the Agent Manager conversation is running.                                     |
| deep-tier     | the strongest model available in the model picker | Recommended pin value — opt-in, not an active default.                                        |
| frontier-tier | the strongest model available in the model picker | No distinct rung above deep-tier; recommended pin value — opt-in, not an active default.      |

The two deep-tier rows are recommended pin values, not active defaults
(selection and override convention in [README.md](README.md)).
Antigravity has no stable CLI model id to pin: model choice is a
human selection in the Agent Manager model picker, so a tier pin here
is a convention for the human dispatcher, not a flag a script passes.

## Role pins

Gemini/Antigravity mapping of the routing defaults adopted in
[claude-code.md](claude-code.md) "Role pins" (spec:
model-routing-native-config). All rows are picker conventions for the
human dispatcher — Antigravity has no flag or frontmatter to pin a
model programmatically.

| Role                                                                  | Antigravity default (model picker)                                            |
| --------------------------------------------------------------------- | ----------------------------------------------------------------------------- |
| session default                                                       | the Agent Manager conversation's model (no plan/execution split exists)       |
| implementation workers                                                | Pro-class — deep-tier adopted default, mirroring claude-code's `opus` pin    |
| explore / codebase-search                                             | Flash-class — the cheapest Flash variant in the picker                        |
| verifier (acceptance evidence; advisory reviewer lane)                | Flash-class                                                                   |
| spec/plan/diff critic                                                 | Pro-class — deep-tier work; a critic pass costs ~1% of a wrong implementation |
| distill workflow                                                      | Pro-class / the strongest model in the picker                                 |
| retry escalation (attempt 2, verifier evidence in prompt)             | the strongest model in the picker — a retry after a deep-tier (Pro-class) attempt failed |
| tournament escalation (attempts 3+, after the frontier retry failed)  | the strongest model in the picker — Antigravity's frontier rung               |

## Headless

No fenced block (README.md's `## Headless` contract, shape 2: no
scriptable relaunch) — confirmed live, not assumed, 2026-07-12 against
`antigravity` v1.107.0. The CLI's `chat` subcommand
(`antigravity chat [prompt] -m agent`) is real, but it is a
**fire-and-forget window launcher, not a synchronous completion API**:
run against a scratch fixture, it returned immediately (exit 0, empty
stdout — no captured response) while spawning a full Electron GUI
session (main process, renderer, GPU process, language server) that
runs the agent asynchronously inside a window. No flag blocks for the
result or writes it anywhere a caller could poll, so there is no
scriptable relaunch whose output this toolkit's consumers (the eval
runner's grade-the-response pattern, drain/autopilot's headless
fallback) could capture. Anything the toolkit would run headlessly in
that sense still becomes an agent the human starts from the Agent
Manager (or via `chat` as a scripted trigger for that same GUI session —
see `## Orchestration`) with the corresponding workflow.

## Orchestration

- **Primitive**: none scripted — sequential markdown workflows
  (`.agents/workflows/`) executed inside one conversation.
- **Invocation surface**: primarily human-dispatched Agent Manager
  parallelism — a fan-out orchestration degrades to a human launch list
  (the human starts each worker agent from the Agent Manager). A script
  can now also trigger one of those sessions itself:
  `antigravity chat "<prompt>" -m agent -n` (confirmed live) opens a
  new-window agent session programmatically — a real scripted
  alternative to manually opening the Agent Manager, useful as
  autopilot's "fire-and-forget, this machine" mechanism. It stays
  launch-only, though: no blocking and no captured result (see
  `## Headless`), so a script still can't learn the outcome without a
  human checking the window or a separate polling mechanism this
  profile does not define.
- **Structured output**: none — workflow args and agent returns are
  free text; no schema validation.
- **Resume**: Agent Manager conversation history plus on-disk artifacts
  (task files, `brain/` artifacts); no journaled replay.
- **Parallelism cap**: however many agents the human chooses to launch;
  no programmatic cap.

## Notes

- **Config locations**: repo — `.agents/skills/`, `.agents/workflows/`,
  `AGENTS.md` (always-on rules), `.agents/hooks.json`; global —
  `~/.gemini/config/skills/`. Older Antigravity builds read `.agent/`
  instead of `.agents/`.
- **Permission-mode equivalents**: the Terminal Execution Policy in the
  Settings UI — Off / Auto / Turbo plus a command deny list. There is
  no repo-checked-in allowlist; for unattended runs, set the deny list
  in Settings (see `antigravity/README.md`).
- **Reference port**: `antigravity/README.md` carries the full
  concept-mapping table; `docs/porting.md` summarizes it alongside the
  other runtimes.
