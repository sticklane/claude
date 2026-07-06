# Runtime profile: gemini-cli

Describes how the abstract tiers and surfaces map onto Google's
gemini-cli. No full port exists (the porting guide, `docs/porting.md`,
is the v1 deliverable); this profile records what a port would target.

## Tiers

| Tier          | Model                                                     | Notes                                                                                                           |
| ------------- | --------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------- |
| scout-tier    | Flash-class model (e.g. `gemini-3.5-flash`, via `-m`)     | Cheap, fast reconnaissance.                                                                                     |
| session-tier  | the CLI's default model                                   | Whatever the interactive session runs; no flag needed.                                                          |
| deep-tier     | Pro-class model (e.g. `gemini-3.1-pro-preview`, via `-m`) | Recommended pin value — opt-in, not an active default.                                                          |
| frontier-tier | the same Pro-class model                                  | No distinct rung above the Pro class exposed by the CLI; recommended pin value — opt-in, not an active default. |

The two deep-tier rows are recommended pin values, not active defaults
(selection and override convention in [README.md](README.md)). Model
ids move fast; check `gemini --help` / release notes for the current
Flash and Pro ids before pinning.

## Role pins

Gemini mapping of the routing defaults adopted in
[claude-code.md](claude-code.md) "Role pins" (spec:
model-routing-native-config). gemini-cli has no `opusplan`-style
plan/execution split, so the session default stays the CLI's default
model; per-role pins pass via `-m`. Same id caveat as above: re-verify
the current Flash and Pro ids before pinning.

| Role                                                                  | Gemini default                                                                        |
| --------------------------------------------------------------------- | ------------------------------------------------------------------------------------- |
| session default                                                       | the CLI's default model (no plan/execution split exists)                              |
| implementation workers                                                | Pro-class (e.g. `gemini-3.1-pro-preview`, via `-m`) — deep-tier adopted default, mirroring claude-code's `opus` pin |
| explore / codebase-search                                             | Flash-class — the CLI's cheapest Flash variant where one is exposed                   |
| verifier (acceptance evidence; advisory reviewer lane)                | Flash-class                                                                           |
| spec/plan/diff critic                                                 | Pro-class — deep-tier work; a critic pass costs ~1% of a wrong implementation         |
| distill workflow                                                      | Pro-class (e.g. `gemini-3.1-pro-preview`, via `-m`)                                   |
| retry escalation (attempt 2, verifier evidence in prompt)             | Pro-class — same tier as attempt 1; the CLI exposes no rung above Pro, so the retry re-runs with the verifier's failure evidence instead of a stronger model |
| tournament escalation (attempts 3+, after the Pro-class retry failed) | Pro-class — the CLI exposes no rung above Pro, so the frontier rung collapses onto it |

## Headless

Non-interactive mode is `-p/--prompt`:

```bash
gemini -p "<prompt>" \
  --allowed-tools <allowlist> \
  --approval-mode yolo -o json
```

- `<prompt>` — a self-contained single-agent prompt, same contract as
  the claude-code template.
- `<allowlist>` — `--allowed-tools` takes tool names to run without
  confirmation; it is deprecated in favor of the Policy Engine
  (`--policy <file>`), which is the durable way to express an
  allowlist.
- `<turn cap>` — no CLI flag exists; set `maxSessionTurns` in
  `~/.gemini/settings.json` (or the project's `.gemini/settings.json`)
  for the run.
- `--approval-mode` replaces claude-code's `--permission-mode`; there
  is no `dontAsk` equivalent that aborts on unapproved tools —
  `yolo` auto-approves everything, so express restrictions through the
  policy/allowlist instead.
- `-o json` (or `stream-json`) gives machine-readable output for
  wrappers.

## Orchestration

- **Primitive**: none native — shell fan-out around headless calls.
- **Invocation surface**: shell scripts wrapping `gemini -p …` per
  worker (one process per parallel task).
- **Structured output**: `-o json` / `-o stream-json` on each call; the
  wrapper script parses and aggregates.
- **Resume**: `--resume <session>` / `--session-file <file>` reattach a
  previous session; the wrapper owns any cross-worker resume logic.
- **Parallelism cap**: whatever the wrapper imposes (e.g. `xargs -P`);
  nothing built in.

## Notes

- **Config locations**: `~/.gemini/settings.json` (global) and
  `.gemini/settings.json` (project); `GEMINI.md` is the CLAUDE.md
  equivalent (always-on context); extensions via `gemini extensions`,
  agent skills via `gemini skills`, hooks via `gemini hooks`.
- **Permission-mode equivalents**: `--approval-mode default` ≈ prompt
  per tool, `auto_edit` ≈ `acceptEdits`, `plan` ≈ read-only plan mode,
  `yolo` ≈ `bypassPermissions`; fine-grained allow/deny lives in the
  Policy Engine.
- **Verification**: command syntax and flags above were verified
  against the `gemini --help` output of gemini-cli v0.46.0 (Homebrew,
  2026-07-03); model ids were taken from that installed version's
  bundle. Re-verify against `gemini --help` before first use on
  another machine or CLI version.
