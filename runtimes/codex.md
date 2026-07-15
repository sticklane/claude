# Runtime profile: codex

Describes how the abstract tiers and surfaces map onto OpenAI's Codex CLI.
`codex/` in this repo is the reference port — a thin overlay reusing
`antigravity/.agents/skills/*` via symlinks, not a third full mirror
(`codex/README.md` has the port's own account; this profile describes it,
it does not replace it).

## Tiers

| Tier          | Model                                                        | Notes                                                                               |
| ------------- | ------------------------------------------------------------ | ------------------------------------------------------------------------------------ |
| scout-tier    | the CLI's cheapest/mini model, via `-m <model>`               | Cheap, fast reconnaissance. Model ids move fast — check `codex -m <TAB>` / release notes for the current mini variant before pinning. |
| session-tier  | the CLI's configured default model (no flag)                  | Whatever the interactive session runs.                                              |
| deep-tier     | the CLI's flagship coding model, via `-m <model>`              | Recommended pin value — opt-in, not an active default. Same id caveat as scout-tier. |
| frontier-tier | the flagship model at raised reasoning effort (`-c model_reasoning_effort=high`) | No distinct model rung above deep-tier; recommended pin value — opt-in, not an active default. |

The two deep-tier rows are recommended pin values, not active defaults
(selection and override convention in [README.md](README.md)). Verify
current model ids against `codex --help` / `-m` completions on the
installed CLI version before pinning — confirmed live here against
`codex-cli 0.144.1`, but ids are not recorded since they change often
(same caution `gemini-cli.md` takes).

## Role pins

Codex mapping of the routing defaults adopted in
[claude-code.md](claude-code.md) "Role pins" (spec:
model-routing-native-config). Codex has no `opusplan`-style plan/execution
split; per-role pins pass via `-m` (and `-c model_reasoning_effort=` for
the effort axis).

| Role                                                                 | Codex default                                                                          |
| --------------------------------------------------------------------- | --------------------------------------------------------------------------------------- |
| session default                                                       | the CLI's configured default model (no plan/execution split exists)                     |
| implementation workers                                                | flagship model, via `-m` — deep-tier adopted default, mirroring claude-code's `opus` pin |
| explore / codebase-search                                             | mini/cheap model, via `-m`                                                              |
| verifier (acceptance evidence; advisory reviewer lane)                 | mini/cheap model, via `-m`                                                              |
| spec/plan/diff critic                                                 | flagship model — deep-tier work; a critic pass costs ~1% of a wrong implementation      |
| distill workflow                                                      | flagship model                                                                          |
| retry escalation (attempt 2, verifier evidence in prompt)             | flagship model at raised reasoning effort — a retry after a deep-tier attempt failed    |
| tournament escalation (attempts 3+, after the retry failed)           | flagship model at raised reasoning effort — Codex's frontier rung                       |

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
- `<tier alias>` — `-m <model>` for the Role pins ladder above; add `-c
  model_reasoning_effort=high` for the frontier rung.
- `--skip-git-repo-check` lets the invocation run outside a git repo (eval
  fixtures always init one, but this keeps the template robust either way).
- `--ephemeral` skips persisting session files — appropriate for one-shot
  relaunches and evals; drop it for a resumable headless session.
- **Discovery is cwd/`--cd`-relative, not git-root-relative**: Codex reads
  skills from `.agents/skills/` under the directory it is invoked in (or
  `--cd <dir>`), confirmed live in `codex/verify-live.sh`. A caller must run
  this template from (or `--cd` into) a directory whose `.agents/skills/`
  holds the skill under test — in this repo, `codex/`.
- **No custom slash commands.** `/breakdown`-style invocation does not
  exist; skills are reached by natural-language description match (15
  reused skills) or by typing the skill's name — see "What degrades on
  Codex" in [../codex/README.md](../codex/README.md).
- **Explicit invocation is unreliable.** The three launch-gated skills
  (`drain`/`build`/`evals`, `allow_implicit_invocation: false`)
  do not reliably invoke through `$name` in `codex exec` yet (upstream
  [openai/codex #19695](https://github.com/openai/codex/issues/19695),
  [#10585](https://github.com/openai/codex/issues/10585),
  [#23454](https://github.com/openai/codex/issues/23454)) — confirmed live,
  `codex/README.md`'s "(c-pos)" result. A headless relaunch of one of the
  four gated stages on Codex is best-effort until those issues close; the
  guard against *unwanted* auto-trigger (the c-neg case) does work.

## Orchestration

- **Primitive**: Codex Subagents (`.codex/agents/` TOML, `/agent`) — a
  delegation/parallelism primitive, not a workflow launcher (see "What
  degrades on Codex" in [../codex/README.md](../codex/README.md)).
- **Invocation surface**: shell scripts wrapping `codex exec …` per worker,
  same shape as the gemini-cli profile; no native fan-out primitive to hand
  a multi-stage script to.
- **Structured output**: `--json` on each call for machine-readable JSONL
  events; `-o <file>` / `--output-last-message` for the final agent message;
  `--output-schema <file>` constrains the final response shape.
- **Resume**: `codex resume` / `codex fork` reattach or branch a previous
  session by id; a wrapper owns any cross-worker resume logic.
- **Parallelism cap**: whatever the wrapper imposes; nothing built in.

## Notes

- **Config locations**: `codex/.agents/skills/` (this repo's port root,
  `.agents/` at a subdirectory — always invoke with `--cd codex` or from
  that cwd); global — `~/.codex/config.toml`. `AGENTS.md` is the CLAUDE.md
  equivalent (always-on context), same as Antigravity.
- **Permission-mode equivalents**: `--sandbox read-only` ≈ plan/read-only
  mode, `--sandbox workspace-write` ≈ `acceptEdits`,
  `--dangerously-bypass-approvals-and-sandbox` ≈ `bypassPermissions`
  (sandboxed use only, per its own `--help` warning).
- **Reference port**: `codex/README.md` carries the full reuse-vs-copy
  account and the live-verification results;
  [`codex/verify-live.sh`](../codex/verify-live.sh) is the re-runnable R5
  check this profile's Headless caveats are drawn from.
- **Verification**: command syntax and flags above were verified against
  `codex exec --help` / `codex --help` output of `codex-cli 0.144.1`
  (installed locally, 2026-07-12). Re-verify against `codex --help` before
  first use on another machine or CLI version.
