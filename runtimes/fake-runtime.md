# Runtime profile: fake-runtime

A minimal, deliberately synthetic runtime profile. It exists to prove the
runtime-agnostic machinery end to end (spec `runtime-agnostic-relaunch`,
R9/R10): dropping a conforming profile here — with a distinct headless
invocation shape — is enough for `workboard.py` to parse that shape out of a
`DRAIN-BATON.md`, with no edits to `workboard.py` itself. It maps no real
CLI; do not select it for a production repo.

## Tiers

| Tier          | Model                | Notes                                            |
| ------------- | -------------------- | ------------------------------------------------ |
| scout-tier    | fake-small           | Cheap, fast reconnaissance.                      |
| session-tier  | the CLI's default    | Whatever the interactive session runs.           |
| deep-tier     | fake-large           | Recommended pin value — opt-in, not a default.   |
| frontier-tier | fake-large           | No distinct rung above deep; opt-in pin value.   |

The two deep-tier rows are recommended pin values, not active defaults
(selection and override convention in [README.md](README.md)).

## Headless

Non-interactive mode is the `run` subcommand:

```bash
fakecli run "<prompt>" \
  --tools <allowlist> \
  --yes --max-steps <turn cap>
```

- `<prompt>` — a self-contained single-agent prompt, same contract as the
  claude-code template.
- `<allowlist>` — tool names the run may use without confirmation.
- `<turn cap>` — the task's `Budget:` turn count when present, else the
  runtime default.

## Orchestration

- **Primitive**: none native — shell fan-out around headless `fakecli run`
  calls, one process per parallel task.
- **Structured output**: none; the wrapper script owns any aggregation.
- **Parallelism cap**: whatever the wrapper imposes; nothing built in.

## Notes

- This profile is synthetic: `fakecli` is not a real binary. It is a fixture
  for the runtime-agnostic relaunch spec's end-to-end demonstration and a
  worked template for authoring a real runtime profile.
