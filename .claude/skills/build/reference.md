# Unattended-execution configs

## Table of contents

Scoped permissions · Bounded goals · Containment ladder · Headless ·
Failure recovery

Runtime-specific commands and permission semantics are verified in
`runtimes/<runtime>.md`; this reference keeps only the shared workflow.

## Scoped permissions for autonomous runs

Select only the active runtime's native permission surface; never write
another runtime's config as a fallback.

For Claude Code, put the autonomy profile in
`.claude/settings.local.json` (personal, gitignored) unless the whole team
wants it — a checked-in `deny` applies to every teammate's attended sessions
too. If the file exists, MERGE the `permissions` key; never overwrite.

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
    "deny": ["Bash(git push *)"]
  }
}
```

Adjust `allow` to the project's verified commands. The `Bash(git ...)`
entries above are git-specific permission prefixes — a jj-based project
would grant its own equivalents; the strings themselves are permission
surface, not prose, and are left as-is. Honesty about what this
buys: permission rules gate commands, not the filesystem — `Bash(npm run *)`
can run any script someone adds to package.json, and a bare `Edit` allow
covers any path. The allowlist prevents the obvious irreversible actions
(push, deploy); hard isolation is the containment ladder below. Rules:
`deny` wins at every level; space-before-`*` is a word boundary
(`Bash(ls *)` matches `ls -la`, not `lsof`); `:*` is equivalent; evaluation
order is deny → ask → allow.

For Codex, use the sandbox and approval policy in `runtimes/codex.md`; it has
no equivalent checked-in per-command allowlist, so do not create
`.claude/settings.local.json`. For Antigravity, use its native execution mode
and sandbox from `runtimes/antigravity.md`; likewise do not invent a Claude
allowlist.

## Bounded goals

Example for a runtime that exposes `/goal`:

```
/goal all acceptance commands in specs/x/tasks/03-api.md pass with output
shown in this conversation, and lint is clean, or stop after 20 turns
```

- When available, the runtime's built-in transcript evaluator (Claude Code:
  Haiku) judges
  only the transcript — the agent must RUN the commands so output is
  visible. It cannot call tools itself.
- Always bound with "or stop after N turns" / a time clause.
- If the runtime has no goal supervisor, use its bounded headless command
  rather than launching another runtime.
- Works headless through the active runtime profile's `## Headless` command;
  pass the bounded condition as the self-contained prompt. Never substitute
  another runtime's CLI.

## Fire-and-forget, unattended

For unattended, fire-and-forget work on this machine, use `/drain` — its
worktree + native awaited-agent coordinator + verdict-only dispatch already
runs that pattern per queued task, with the retry ladders and verification
gates a bare background agent lacks.

## Containment ladder

1. Worktree: isolates the diff, not the machine. Default for parallel work.
   Codebase-Memory processes share the toolkit cache but each launch is
   restricted by `CBM_ALLOWED_ROOT` to its own Git root. Query it first for
   structure; if unavailable in the worktree, use bounded `rg` plus small
   reads and report that coverage was unavailable. Never copy graph state
   into a checkout.
2. `/sandbox` (OS-level: Seatbelt/bubblewrap): filesystem writes limited to
   CWD, per-domain network approval.
3. Network-isolated container (the published devcontainer's default-deny
   iptables firewall): the only place `--dangerously-skip-permissions` is
   defensible — and even there, credentials inside the container are
   exfiltratable by a malicious repo. Prefer auto mode + allowlists.

## Headless (CI, scripts, cron)

The headless worker gets a SELF-CONTAINED prompt — no skill references and no
subagent fan-out (keep it single-agent). Render the launch only from the
active runtime's `runtimes/<runtime>.md` `## Headless` section. That profile
owns its executable, permissions/sandbox flags, output format, authentication,
and turn/time bounds; shared skill text never supplies a fallback CLI.

The prompt itself is portable: read the named task, write failing tests first
when production rigor applies, implement until every acceptance command
passes, show the evidence, commit on the named task branch, do not push, and
return verdict + evidence per criterion + files changed. Before launch,
confirm the active profile's permission or sandbox mechanism admits every
acceptance command and fails closed or stops clearly when it cannot.

## Failure recovery

- A failed autonomous run is evidence about the task file, not a debugging
  invitation: fix the spec/task, discard the branch, relaunch clean.
- Repeated gate blocks (Stop-hook cap, goal/headless bound) mean the task was
  under-specified or the check is wrong — both are human decisions.
