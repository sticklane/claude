# Unattended-execution configs

Verified against code.claude.com/docs (permissions, headless, goal,
sandboxing) as of July 2026.

## Scoped permissions for autonomous runs

`.claude/settings.json` (commit it — the whole team's agents inherit it):

```json
{
  "permissions": {
    "allow": [
      "Bash(npm run *)",
      "Bash(npx tsc *)",
      "Bash(git add *)",
      "Bash(git commit *)",
      "Bash(git checkout *)",
      "Bash(git worktree *)"
    ],
    "deny": [
      "Bash(git push *)",
      "WebFetch"
    ]
  }
}
```

Rules: `deny` wins at every level; space-before-`*` is a word boundary
(`Bash(ls *)` matches `ls -la`, not `lsof`); `:*` is equivalent. Evaluation
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

Delegate with worktree isolation and a self-contained prompt:

> Execute the task in <file> following .claude/skills/build/SKILL.md.
> Work only in this worktree, commit to task/NN-<slug>, do not push.
> Final message: verdict, per-criterion evidence, branch, files changed.

Requires Claude Code v2.1.172+ for the worker to spawn its own
scouts/verifiers; otherwise use headless dispatch below.

## Headless (CI, scripts, cron)

```bash
claude -p "Execute the task in specs/x/tasks/03-api.md per \
.claude/skills/build/SKILL.md. Commit to task/03-api. Do not push." \
  --allowedTools "Read,Edit,Write,Bash(npm run *),Bash(git add *),Bash(git commit *)" \
  --permission-mode dontAsk \
  --max-turns 40 \
  --output-format json
```

- `dontAsk` is the CI baseline: unapproved tools abort instead of hanging.
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
