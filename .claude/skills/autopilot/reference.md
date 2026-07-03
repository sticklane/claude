# Unattended-execution configs

Verified against code.claude.com/docs (permissions, headless, goal,
sandboxing) as of July 2026.

## Scoped permissions for autonomous runs

Put the autonomy profile in `.claude/settings.local.json` (personal,
gitignored) unless the whole team wants it — a checked-in `deny` applies to
every teammate's attended sessions too. If the file exists, MERGE the
`permissions` key; never overwrite.

```json
{
  "permissions": {
    "allow": [
      "Bash(npm run *)",
      "Bash(npx tsc *)",
      "Bash(git add *)",
      "Bash(git commit *)",
      "Bash(git worktree *)"
    ],
    "deny": [
      "Bash(git push *)"
    ]
  }
}
```

Adjust `allow` to the project's verified commands. Honesty about what this
buys: permission rules gate commands, not the filesystem — `Bash(npm run *)`
can run any script someone adds to package.json, and a bare `Edit` allow
covers any path. The allowlist prevents the obvious irreversible actions
(push, deploy); hard isolation is the containment ladder below. Rules:
`deny` wins at every level; space-before-`*` is a word boundary
(`Bash(ls *)` matches `ls -la`, not `lsof`); `:*` is equivalent; evaluation
order is deny → ask → allow.

## Bounded goals

```
/goal all acceptance commands in specs/x/tasks/03-api.md pass with output
shown in this conversation, and lint is clean, or stop after 20 turns
```

- The evaluator (Haiku) judges only the transcript — the agent must RUN the
  commands so output is visible. It cannot call tools itself.
- Always bound with "or stop after N turns" / a time clause.
- Works headless: `claude -p "/goal <condition>"` runs the loop to
  completion in one invocation.

## Background worktree agent (fire-and-forget, local)

The mechanism, concretely: delegate with the **Agent tool** — subagent type
`general-purpose`, `isolation: worktree` (fresh checkout, auto-dispatched),
run in background so the session stays free. Completion arrives as a
notification in the main conversation; no polling. At dispatch time,
resolve build's SKILL.md to a concrete path —
`.claude/skills/build/SKILL.md` when the toolkit is in-repo, otherwise
the plugin cache path found at dispatch — and substitute it for
`<build-skill-path>` (workers cannot invoke `disable-model-invocation`
skills, so the prompt must carry a readable path). Prompt template:

> Execute the task in <file> following the build skill's procedure, as
> written in <build-skill-path> (resolved at dispatch).
> Work only in your worktree, commit to task/NN-<slug>, do not push.
> The task file's `Budget:` line is a ceiling, not a target: when
> remaining work clearly exceeds the remaining budget, stop with verdict
> BLOCKED "over budget" rather than grind on.
> Final message: verdict, per-criterion evidence, branch, files changed.

Requires Claude Code v2.1.172+ for the worker to spawn its own
scouts/verifiers; on older versions use headless dispatch below.

## Headless (CI, scripts, cron)

The headless worker gets a SELF-CONTAINED prompt — no skill references, no
subagent fan-out (keep it single-agent), and `--allowedTools` derived from
the task file's actual acceptance commands plus the tools the steps need:

```bash
claude -p "Read specs/x/tasks/03-api.md. Implement it: write the failing
tests first, then code until the acceptance commands pass. Run every
acceptance command and show the output. Commit to task/03-api with the
task file updated. Do not push. Final output: verdict, evidence per
criterion, files changed." \
  --allowedTools "Read,Grep,Glob,Edit,Write,Bash(npm run *),Bash(npx jest *),Bash(git add *),Bash(git commit *),Bash(git checkout -b *)" \
  --permission-mode dontAsk \
  --max-turns 40 \
  --output-format json
```

- Before launching, check each acceptance command in the task file is
  covered by an `--allowedTools` entry — in `dontAsk` mode, unapproved
  tools abort the run (that's the point: fail closed).
- `--output-format json` includes `total_cost_usd` and `session_id`.
- Auth for CI: `claude setup-token` → `CLAUDE_CODE_OAUTH_TOKEN`.
- Recurring: `/loop 30m <prompt>` locally (auto-expires after 7 days) or
  GitHub Actions `on: schedule` with `anthropics/claude-code-action@v1`
  plus `claude_args: --max-turns 10` and a workflow-level timeout.

## Containment ladder

1. Worktree: isolates the diff, not the machine. Default for parallel work.
2. `/sandbox` (OS-level: Seatbelt/bubblewrap): filesystem writes limited to
   CWD, per-domain network approval.
3. Network-isolated container (the published devcontainer's default-deny
   iptables firewall): the only place `--dangerously-skip-permissions` is
   defensible — and even there, credentials inside the container are
   exfiltratable by a malicious repo. Prefer auto mode + allowlists.

## Failure recovery

- A failed autonomous run is evidence about the task file, not a debugging
  invitation: fix the spec/task, discard the branch, relaunch clean.
- Repeated gate blocks (Stop-hook cap, /goal turn bound) mean the task was
  under-specified or the check is wrong — both are human decisions.
