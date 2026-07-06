# Runtime profile: antigravity

Describes how the abstract tiers and surfaces map onto Antigravity. The
`antigravity/` directory in this repo is the reference port (skills,
workflows, AGENTS.md, hooks); this profile describes it, it does not
replace it.

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

None exists. Antigravity has no non-interactive command template — the
Agent Manager launches agents instead. Anything the toolkit would run
headlessly (drain/autopilot fallback workers) becomes an agent the
human starts from the Agent Manager with the corresponding workflow.

## Orchestration

- **Primitive**: none scripted — sequential markdown workflows
  (`.agents/workflows/`) executed inside one conversation.
- **Invocation surface**: human-dispatched Agent Manager parallelism —
  a fan-out orchestration degrades to a human launch list (the human
  starts each worker agent from the Agent Manager).
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
