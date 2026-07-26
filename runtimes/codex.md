# Runtime profile: codex

Describes how the abstract tiers and surfaces map onto OpenAI's Codex CLI.
Codex discovers the shared `.claude/skills/*` sources through repository
symlinks under `.agents/skills/`; `codex/README.md` explains that shared-source
layout.

## Tiers

| Tier          | Model                                                        | Notes                                                                               |
| ------------- | ------------------------------------------------------------ | ------------------------------------------------------------------------------------ |
| scout-tier    | the CLI's cheapest/mini model, via `-m <model>`               | Cheap, fast reconnaissance. Model ids move fast — check `codex -m <TAB>` / release notes for the current mini variant before pinning. |
| session-tier  | the CLI's configured default model (no flag)                  | Whatever the interactive session runs.                                              |
| deep-tier     | `gpt-5.6-sol` at high reasoning effort                        | Current flagship coding model for implementation and criticism.                     |
| frontier-tier | `gpt-5.6-sol` at ultra reasoning effort                       | Reserved for sanctioned escalation, not automatically selected by Ultra orchestration. |

Ultracode maps to the orchestration section below, independently of model
tiering. A stage selects `gpt-5.6-sol` with `model_reasoning_effort=ultra`
only when token discipline calls for frontier-tier escalation. Re-verify the
model id when the installed Codex model catalog changes.

## Role pins

Codex mapping of the routing defaults adopted in
[claude-code.md](claude-code.md) "Role pins" (spec:
model-routing-native-config). Codex has no `opusplan`-style plan/execution
split; per-role pins pass via `-m` (and `-c model_reasoning_effort=` for
the effort axis).

| Role                                                                 | Codex default                                                                          |
| --------------------------------------------------------------------- | --------------------------------------------------------------------------------------- |
| session default                                                       | the CLI's configured default model (no plan/execution split exists)                     |
| implementation workers                                                | `gpt-5.6-sol` at high reasoning effort                                                  |
| explore / codebase-search                                             | mini/cheap model, via `-m`                                                              |
| verifier (acceptance evidence; advisory reviewer lane)                 | mini/cheap model, via `-m`                                                              |
| spec/plan/diff critic                                                 | `gpt-5.6-sol` at high reasoning effort                                                   |
| distill workflow                                                      | `gpt-5.6-sol` at high reasoning effort                                                   |
| retry escalation (attempt 2, verifier evidence in prompt)             | `gpt-5.6-sol` at ultra reasoning effort                                                  |
| tournament escalation (attempts 3+, after the retry failed)           | `gpt-5.6-sol` at ultra reasoning effort                                                  |

## Headless

Non-interactive mode is `codex exec` (confirmed live against
`codex-cli 0.144.1`; flags per `codex exec --help`):

```bash
codex exec --skip-git-repo-check --ephemeral --sandbox workspace-write "<prompt>"
```

- `<prompt>` — a self-contained single-agent prompt, same contract as the
  claude-code template. Passed as the trailing positional argument (or via
  stdin), never combined with `-`.
- `<allowlist>` — no direct equivalent. Codex has no per-tool allowlist
  flag; `--sandbox {read-only,workspace-write,danger-full-access}` is the
  closest analogue (coarse-grained: filesystem write + network posture, not
  a tool-by-tool list). A consumer that needs the resolved allowlist for
  bookkeeping may pass it through `ALLOWED_TOOLS`/env, but it does not map
  onto a CLI flag here — this template omits the placeholder rather than
  fabricate a flag that doesn't exist (`## Headless` contract in
  [README.md](README.md) requires only `<prompt>`).
- `<turn cap>` — no CLI flag; Codex has its own internal step budget, not a
  turn-count flag.
- `<tier alias>` — `-m gpt-5.6-sol -c model_reasoning_effort=high` for
  deep-tier; change the effort value to `ultra` only for frontier-tier or a
  sanctioned escalation.
- `--skip-git-repo-check` lets the invocation run outside a git repo (eval
  fixtures always init one, but this keeps the template robust either way).
- `--ephemeral` skips persisting session files — appropriate for one-shot
  relaunches and evals; drop it for a resumable headless session.
- **Discovery is cwd/`--cd`-relative, not git-root-relative**: Codex reads
  skills from `.agents/skills/` under the directory it is invoked in (or
  `--cd <dir>`). Run from, or `--cd` into, the repository root.
- **No custom slash commands.** `/breakdown`-style invocation does not
  exist; Codex discovers every shared skill from the repository-root
  `.agents/skills/` symlinks and invokes it by description or skill name.
  Launch authorization remains in the shared skill instructions.

## Orchestration

- **Primitive**: Codex collaboration subagents (`spawn_agent`,
  `wait_agent`, `followup_task`) managed by the main session.
- **Ultra-equivalent shape**: the main session compiles the same logical
  stages as Claude Workflow—fan-out, barrier/reduction, verification, and a
  bounded fix round—into subagent calls. Read-only stages may run in
  parallel. Codex drain provisions an explicit git worktree for each writing
  subagent and passes its absolute path to the worker and reviewers; writing
  stages run serially, then the orchestrator merges and removes the worktree.
- **Context and tiering**: dispatch compact self-contained prompts with
  `fork_turns: "none"`. Keep each stage's role pin; Ultra orchestration does
  not promote every child to frontier-tier.
- **Gate placement**: workers and bounded fix rounds run acceptance plus
  targeted tests. After the parallel verifier/critic barrier resolves, the
  main session runs the canonical project gate once before merge.
- **Structured output**: `--json` on each call for machine-readable JSONL
  events; `-o <file>` / `--output-last-message` for the final agent message;
  `--output-schema <file>` constrains the final response shape.
- **Resume**: bd and committed artifacts are the durable checkpoint. A
  restarted orchestrator re-reads them before dispatch. Individual Codex
  sessions may also use `codex resume` / `codex fork`.
- **Parallelism cap**: four live agents including the main session in the
  current Codex collaboration runtime; the orchestrator must honor the
  smaller limit if the runtime reports one.

## Notes

- **Config locations**: repository `.agents/skills/`; global —
  `~/.codex/config.toml`. `AGENTS.md` is the always-on context surface.
- **Permission-mode equivalents**: `--sandbox read-only` ≈ plan/read-only
  mode, `--sandbox workspace-write` ≈ `acceptEdits`,
  `--dangerously-bypass-approvals-and-sandbox` ≈ `bypassPermissions`
  (sandboxed use only, per its own `--help` warning).
- **Runtime guide**: `codex/README.md` explains shared skill discovery and
  the common bd/ctx/spec data layer.
- **Verification**: command syntax and flags above were verified against
  `codex exec --help` / `codex --help` output of `codex-cli 0.144.1`
  (installed locally, 2026-07-12). Re-verify against `codex --help` before
  first use on another machine or CLI version.
