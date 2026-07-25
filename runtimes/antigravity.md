# Runtime profile: antigravity

Describes how the abstract tiers and native orchestration surfaces map onto
Antigravity. `antigravity/README.md` explains the bd/ctx/spec data layer used
after the procedure-copy tree was retired.

"Antigravity" always means the `antigravity-cli` package (binary `agy`)
plus the Agent Manager GUI — never the GUI alone. **Name collision, verify
before use**: this machine also has the Antigravity.app *bundle's own*
launcher scripts symlinked as `antigravity` and `agy` under
`~/.antigravity/antigravity/bin/`, and that directory sits earlier in
`$PATH` than Homebrew's `/opt/homebrew/bin/agy` — so a plain `agy` can
silently resolve to the wrong tool. The two are easy to tell apart:
`agy --version` on the real `antigravity-cli` prints one bare line (e.g.
`1.1.1`); the app-bundle impostor prints three (an app version like
`1.107.0`, a commit hash, an arch). If in doubt, use the full path
(`/opt/homebrew/bin/agy` on this machine) rather than the bare command.

## Tiers

| Tier          | Model                                              | Notes                                                                             |
| ------------- | --------------------------------------------------- | ---------------------------------------------------------------------------------- |
| scout-tier    | `Gemini 3.5 Flash (Low)`, via `--model`              | Cheap, fast reconnaissance — cheapest entry in `agy models`' output.               |
| session-tier  | the CLI's configured default model (no `--model`)   | Whatever the interactive session runs.                                             |
| deep-tier     | `Claude Opus 4.6 (Thinking)` or `Gemini 3.1 Pro (High)`, via `--model` | Recommended pin value — opt-in, not an active default. Either is a legitimate flagship-tier pin; `agy models` lists both plus `Claude Sonnet 4.6 (Thinking)` and `GPT-OSS 120B (Medium)`. |
| frontier-tier | same as deep-tier                                   | No distinct rung above deep-tier exposed by the CLI; recommended pin value — opt-in, not an active default. |

The two deep-tier rows are recommended pin values, not active defaults
(selection and override convention in [README.md](README.md)). Model
names are exact strings from `agy models`' output (confirmed live,
`antigravity-cli` 1.1.1, 2026-07-12) — pass them to `--model` verbatim,
quoted; re-verify against `agy models` before pinning, since the roster
changes as models are added/retired. Unlike the picker-only model in this
profile's previous version, `--model` genuinely lets a script pin a model
— no live test of `--model` accepting these exact strings has been run
yet (only `-p` with no `--model` override was confirmed); treat the exact
invocation as unverified until checked.

## Role pins

Antigravity mapping of the routing defaults adopted in
[claude-code.md](claude-code.md) "Role pins" (spec:
model-routing-native-config). Antigravity has no `opusplan`-style
plan/execution split; per-role pins pass via `--model` (confirmed to
exist as a flag; exact value acceptance unverified — see Tiers above).

| Role                                                                 | Antigravity default                                                                      |
| --------------------------------------------------------------------- | -------------------------------------------------------------------------------------------- |
| session default                                                       | the CLI's configured default model (no plan/execution split exists)                          |
| implementation workers                                                | `Claude Opus 4.6 (Thinking)`, via `--model` — deep-tier adopted default matching claude-code's `opus` pin |
| explore / codebase-search                                             | `Gemini 3.5 Flash (Low)`, via `--model`                                                      |
| verifier (acceptance evidence; advisory reviewer lane)                | `Gemini 3.5 Flash (Low)`, via `--model`                                                      |
| spec/plan/diff critic                                                 | `Claude Opus 4.6 (Thinking)` — deep-tier work; a critic pass costs ~1% of a wrong implementation |
| distill workflow                                                      | `Claude Opus 4.6 (Thinking)`                                                                 |
| retry escalation (attempt 2, verifier evidence in prompt)             | `Gemini 3.1 Pro (High)` — same tier as attempt 1; the CLI exposes no rung above deep-tier, so the retry re-runs with the verifier's failure evidence instead of a stronger model |
| tournament escalation (attempts 3+, after the retry failed)           | `Gemini 3.1 Pro (High)` — the CLI exposes no rung above deep-tier, so the frontier rung collapses onto it |

## Headless

Non-interactive mode is `agy -p` / `--print` (confirmed live,
`antigravity-cli` 1.1.1, 2026-07-12 — both a plain reply and an isolated
file-edit fixture completed successfully):

```bash
/opt/homebrew/bin/agy -p "<prompt>" --new-project --mode accept-edits --sandbox
```

**The absolute path is load-bearing, not decoration.** A bare `agy` was
tried first and failed live: invoked from inside a subprocess (the eval
runner), it silently resolved to the app-bundle impostor (`Warning: 'p' is
not in the list of known options, but still passed to Electron/Chromium`),
returned in ~2s instead of blocking for a real model turn, and produced no
usable output — the PATH-shadow risk noted above is not theoretical, it
reproduced on the first real end-to-end attempt. Use the absolute path
confirmed on this machine; re-resolve it (`brew --prefix`, or wherever
`antigravity-cli` installs) rather than assuming this path on another
machine.

**`--new-project` fixes the workspace-isolation defect — confirmed live,
safe for isolated/unattended use.** The earlier finding (below, kept for
the record) was that `agy -p` without `--new-project` did not confine
itself to the invoking directory. Live-tested 2026-07-13,
`antigravity-cli` 1.1.1: two back-to-back `agy -p ... --new-project`
invocations, each from its own fresh scratch git repo with a distinct
prompt ("create marker.txt" / "create second.txt"), each produced exactly
the requested file in its own invoking directory and nothing else —
no cross-contamination between the two runs, no writes anywhere in this
toolkit's real checkout (`git status` clean before and after both runs,
repo-wide `find -newermt` turned up nothing). This matches the leading
theory below (workspace reuse, not path miscalculation) and confirms
`--new-project` is the fix, not just a plausible one. `evals/run.sh` no
longer hard-blocks this runtime as a result (see its own history for the
prior block); codex and claude-code confirm the same
invoking-cwd confinement by a different mechanism (`--cd`/cwd-relative
discovery, no reuse concept to begin with).

Prior finding, for the record — **do not drop `--new-project` from the
template above; this is why it's there.** Live-tested end to end via the
eval runner (`(cd "$EVAL_DIR" && /opt/homebrew/bin/agy -p ...)` with no
`--new-project`, `$EVAL_DIR` a fresh `mktemp -d` with its own `git init`):
the process did NOT confine itself to `$EVAL_DIR`. It instead edited real,
tracked files in this toolkit's own checkout
(`tests/fixtures/workboard/demo-repo/specs/demo/{SPEC.md,tasks/01-thing.md}`,
plus created a new `02-other-thing.md`) — a path with no filesystem
relationship to `$EVAL_DIR` at all. Reverted cleanly (uncommitted,
`git checkout --` + `rm` the new file; the affected test still passes).
Leading theory, now corroborated: `-p` without `--new-project` reused a
stale "last active workspace" from an unrelated manual test run minutes
earlier in this same repo, rather than scoping to the invoking cwd —
consistent with the top-level CLI's own `-r`/`--reuse-window` "last active
window" language and the GUI's session-reuse model bleeding into `-p`
mode absent an explicit fresh-workspace flag.

- `<prompt>` — a self-contained single-agent prompt, same contract as the
  claude-code template. Passed via `-p`/`--print` (`--prompt` is a
  documented alias for the same flag).
- `<allowlist>` — no per-tool allowlist flag exists. `--sandbox` ("Run in
  a sandbox with terminal restrictions enabled") is the closest analogue
  — coarse-grained, not a tool-by-tool list, same gap the codex and
  gemini-cli profiles note for their own runtimes. `--mode accept-edits`
  auto-approves edits without prompting; `--dangerously-skip-permissions`
  bypasses ALL tool-permission prompts (claude-code's `bypassPermissions`
  analogue — sandboxed use only, per its own `--help` naming). There is
  no `dontAsk`-equivalent that aborts on an unapproved tool instead of
  auto-approving or hanging.
- `<turn cap>` — no CLI flag; `--print-timeout` (default `5m0s`) bounds
  wall-clock wait instead of a turn count.
- `<tier alias>` — `--model "<exact name from agy models>"` for the Role
  pins ladder above (unverified — see Tiers).
- **Discovery walks up to find the workspace root**, not strictly
  cwd/`--cd`-relative like Codex: invoked from `antigravity/` in this
  repo, it treated `/Users/sjaconette/claude` (one level up, the git
  root) as "the project" in its own summary, while still finding and
  running the skill that only exists under `antigravity/.agents/skills/`
  — i.e. it discovered skills relative to the actual invocation cwd even
  while reporting a workspace root above it. Run it from (or `--add-dir`
  into) `antigravity/`, matching Codex's `--cd codex` convention, until a
  more precise discovery-root test is run.
- **Skill invocation** works the same way Codex's does (both consume the
  Agent Skills standard antigravity defines): no custom slash commands,
  reached by natural-language description match. Unlike Codex's
  explicit-`$name` invocation (confirmed unreliable there), whether an
  explicit invocation syntax exists and works here has not been tested —
  the one live check exercised auto-trigger only.
- **Structured output**: no `--json`/`-o` flag in `agy --help`; the
  response prints as prose/markdown to stdout, sometimes pointing at a
  generated artifact file under `~/.gemini/antigravity-cli/brain/<uuid>/`
  (confirmed live — see Orchestration).

## Orchestration

- **Primitive**: Native subagents (`invoke_subagent` / `define_subagent` with
  `Workspace: 'branch'` or `'share'`) represent the **Gemini Ultracode equivalent**
  for staged fan-out, independent verification, and parallel panel runs;
  unattended / headless runs can also execute via `agy -p` scripts.
- **Invocation surface**: `invoke_subagent` (interactive / in-harness) or `agy -p "<prompt>"`
  per worker (headless CLI, confirmed live). Shell scripts and subagent dispatches
  wrap parallel tasks; the Agent Manager GUI remains available for human-dispatched
  parallelism when a human wants to watch.
- **Ultra-equivalent shape**: stage role, not Ultra itself, selects the model.
  Pass compact self-contained prompts rather than the parent transcript.
  Use `Workspace: 'branch'` for writers and serialize any `Workspace: 'share'`
  writer; read-only panels may run in parallel. Workers and bounded fix rounds
  run acceptance plus targeted tests, then the orchestrator runs the canonical
  project gate once after the verifier/critic barrier.
- **Structured output**: none — no `--json` flag; responses are
  free-text/markdown, sometimes with a linked artifact file (see
  Headless). No schema validation.
- **Resume**: `--continue`/`-c` (most recent conversation) or
  `--conversation <id>` (resume by id) reattach a previous session,
  confirmed present in `--help` (not live-tested); a wrapper owns any
  cross-worker resume logic. `brain/<uuid>/` artifact directories
  (confirmed live, under `~/.gemini/antigravity-cli/brain/`) persist
  generated files across a session.
- **Parallelism cap**: whatever the wrapper imposes; nothing built in.

## Notes

- **Config locations**: repo — `.agents/skills/`, `.agents/workflows/`,
  `AGENTS.md` (always-on rules), `.agents/hooks.json`; global —
  `~/.gemini/config/skills/`, `~/.gemini/antigravity-cli/brain/`
  (generated-artifact storage, confirmed live). Older Antigravity builds
  read `.agent/` instead of `.agents/`.
- **Permission-mode equivalents**: `--mode plan` ≈ read-only planning,
  `--mode accept-edits` ≈ `acceptEdits`, `--dangerously-skip-permissions`
  ≈ `bypassPermissions` (sandboxed use only, per its own naming),
  `--sandbox` layers terminal restrictions on top of any mode. The GUI's
  Terminal Execution Policy (Settings UI: Off/Auto/Turbo + a command deny
  list) is the separate interactive-session equivalent; there is no
  repo-checked-in allowlist file either way.
- **The `agy`/`antigravity` name collision is machine-specific but
  real**: confirmed on this machine (`~/.antigravity/antigravity/bin`
  before `/opt/homebrew/bin` in `$PATH`); verify PATH order or use an
  absolute path before trusting a bare `agy` invocation elsewhere.
- **Runtime guide**: `antigravity/README.md` explains the common bd/ctx/spec
  data layer and records why the copied procedure tree was retired.
- **Verification**: `-p` and model listing were confirmed live against
  `antigravity-cli` 1.1.1 (Homebrew cask, installed 2026-07-11) on
  2026-07-12. `--new-project` workspace isolation was confirmed live on
  2026-07-13 (two
  back-to-back isolated invocations, no cross-contamination, no stray
  writes to the real checkout — see Headless above). `--model`,
  `--mode`, `--dangerously-skip-permissions`, `--continue`/
  `--conversation`, and exact discovery-root semantics are documented
  from `--help` output but not yet exercised live — re-verify before
  relying on them, same caution the gemini-cli and codex profiles take
  for their own unverified flags.
