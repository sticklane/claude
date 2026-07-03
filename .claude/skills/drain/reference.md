# /drain reference

Loaded on demand. Contains the classification checklist, status semantics,
the exact worker prompt, and the headless fallback.

## When NOT to drain (the peripheral/core gate)

Drain a task only if every box checks (from the playbook's task
classification — peripheral work runs unattended, core work is watched):

- [ ] Not core business logic, auth, payments, billing, or data migration
- [ ] Acceptance criteria are runnable commands (not "looks right")
- [ ] A wrong implementation is cheap to discard (branch-isolated, no
      side effects outside the repo)
- [ ] No credentials or external services beyond what CI already uses

Anything unchecked: pull that task out of the queue and run it attended
with /build; drain the rest.

## Status field semantics

The task file's `Status:` line is the queue's only state store.

| Status | Meaning | Written by |
|---|---|---|
| `pending` | dispatch when dependencies are done | /breakdown (initial) |
| `in-progress` | a worker owns it (the lock-file claim) | /drain, at dispatch |
| `done` | branch merged, project gates green | /drain, at collect |
| `deferred` | waiting on a human answer in the file | the worker |
| `blocked` | technical blocker; task needs amending | /drain, at collect |
| `failed` | two failed attempts; evidence recorded | /drain, at collect |

On startup, any `in-progress` with no live worker is a stale lock — reset
it to `pending` (its worktree/branch, if present, is discarded first:
slot-machine recovery, never resumed).

## Worker prompt (verbatim, fill the <>)

> Execute the task in <task-file> following the build skill's procedure
> exactly (in-repo: .claude/skills/build/SKILL.md; plugin install: invoke
> /agentic:build or read build's SKILL.md from the plugin's skills
> directory): scouts for exploration, tests first where criteria are
> test-shaped, run every acceptance command, standard gates, then commit
> to a branch named task/NN-<slug>. Work only in your worktree; do not
> push.
>
> You are unattended — never ask the human anything. If you hit ambiguity
> a human must resolve (contradictory requirements, a product choice the
> spec leaves open, missing access), do NOT guess and do NOT improvise:
> append the question to the task file under a "## Deferred questions"
> heading, change its Status line to "deferred", and stop with verdict
> DEFERRED. If an "## Answers" section exists, treat it as binding
> spec.
>
> Your final message must be only: verdict (DONE / BLOCKED / DEFERRED),
> acceptance evidence per criterion (command + result), branch name,
> files changed. If BLOCKED, one paragraph on why.

## Deferred question format (what workers write)

```markdown
## Deferred questions

- [2026-07-03 /drain] The spec says "notify the user" but doesn't say
  email or in-app. Blocking: task 04's acceptance test asserts a
  delivery channel.
```

Answers go under `## Answers` in the same file; the orchestrator flips
`Status: deferred` → `pending` once an answer lands.

## Relaunch-with-evidence prompt (slot machine, attempt 2)

Append to the worker prompt:

> A previous attempt failed after implementation: <merge conflict on
> <files> | gate failure: <command + output tail>>. Its branch was
> discarded; do not look for it. Avoid the recorded failure.

## Headless fallback (no background agents / older CLI)

One task at a time, from the repo root:

```bash
git worktree add ../<repo>-task-NN task/NN-<slug>
cd ../<repo>-task-NN
claude -p "<worker prompt above>" \
  --allowedTools "Read,Edit,Write,Glob,Grep,Bash(<verified test/lint/build cmds>),Bash(git add *),Bash(git commit *)" \
  --permission-mode dontAsk --max-turns 80
```

`dontAsk` makes unapproved tools abort instead of hanging — the CI
baseline from the playbook's mechanism ladder. Collect the printed verdict,
then merge/gate/update Status exactly as in step 3, and
`git worktree remove` the checkout.
