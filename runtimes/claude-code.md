# Runtime profile: claude-code

The default profile. It reproduces the toolkit's behavior exactly as it
ships today — a repo with no `.claude/runtime.md` (see
[README.md](README.md)) runs this profile unchanged.

## Tiers

| Tier | Model | Notes |
|---|---|---|
| scout-tier | Haiku (`haiku`) at `effort: low` | Cheap, fast, read-only reconnaissance — the `scout` agent's default. |
| session-tier | inherit | The conversation's own model; whatever the session runs. |
| deep-tier | Opus 4.8 (`claude-opus-4-8`; Agent-tool short name `opus`) | Recommended pin value — opt-in, not an active default. |
| frontier-tier | Fable (`claude-fable-5`; Agent-tool short name `fable`) | Recommended pin value — opt-in, not an active default. |

The two deep-tier rows are recommended pin values, not active defaults:
dispatchers route deep-tier/frontier-tier work to these models only when
a repo's `.claude/runtime.md` pins the tier explicitly (the selection
and override convention lives in [README.md](README.md)). With no pin,
deep and frontier work inherits the session model — today's behavior,
zero new cost.

## Headless

Today's non-interactive contract, as used by the drain and autopilot
headless fallbacks (`.claude/skills/drain/reference.md` is the
authoritative copy; this template restates its contract without
changing it):

```bash
claude -p "<prompt>" \
  --allowedTools "<allowlist>" \
  --permission-mode dontAsk --max-turns <turn cap>
```

- `<prompt>` — a self-contained single-agent prompt (no skill
  references, no subagent fan-out; the allowlist has no Task tool, so
  scout/verifier calls would abort under `dontAsk`).
- `<allowlist>` — e.g. `"Read,Edit,Write,Glob,Grep,Bash(<verified
  test/lint/build cmds>),Bash(git add *),Bash(git commit *)"`.
- `<turn cap>` — the task's `Budget:` turn count when present, else 80;
  the hard cap behind the prompt's soft stop.

`dontAsk` makes unapproved tools abort instead of hanging — the CI
baseline from the playbook's mechanism ladder.

## Orchestration

- **Primitive**: the Workflow tool (multi-agent orchestration in the
  harness).
- **Invocation surface**: named deterministic scripts in
  `.claude/workflows/`, fired only on the explicit human "ultracode"
  opt-in (docs/human-gates.md, reason 5 — orchestration scripts are
  human-gated so injected text can never launch a fleet).
- **Structured output**: schema-validated returns from workflow steps.
- **Resume**: journaled — an interrupted run resumes from its journal
  with cached-prefix replay rather than restarting.
- **Parallelism cap**: per-run concurrency cap set on the workflow run.

## Notes

- **Config locations**: project — `.claude/settings.json` (shared) and
  `.claude/settings.local.json` (per-machine), `CLAUDE.md`,
  `.claude/skills/`, `.claude/agents/`, `.claude/rules/`; user-global —
  `~/.claude/settings.json`, `~/.claude/CLAUDE.md`.
- **Permission modes**: `default` (prompt per tool), `acceptEdits`
  (auto-approve file edits), `plan` (read-only), `dontAsk` (unapproved
  tools abort — the headless/CI mode above), `bypassPermissions`
  (approve everything; sandboxed use only).
- **Runtime selection / tier overrides**: `.claude/runtime.md`,
  documented once in [README.md](README.md).
