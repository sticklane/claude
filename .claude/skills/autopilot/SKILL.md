---
name: autopilot
description: Launches a task for unattended execution with verification gates - classifies whether the task is safe to run autonomously, scopes permissions, sets a bounded goal, and starts it in the background or headless. For walking away from well-specified, peripheral work.
argument-hint: "[path/to/task.md]"
disable-model-invocation: true
---

Run the task at $ARGUMENTS without supervision. Autonomy is earned by
verification, not granted by optimism: an unattended agent is only as safe
as the gates around it. Configs are in [reference.md](reference.md).

## 1. Classify the task (go/no-go)

Autonomous execution fits: peripheral features, prototypes, migrations with
mechanical verification, anything with runnable acceptance criteria and no
irreversible actions. It does NOT fit: core business logic, security-
sensitive code, ambiguous specs, tasks whose verification is "looks right".
That split — auto-accept for the edges, synchronous supervision for the
core — is how Anthropic's own teams draw the line. If the task is on the
wrong side, say so and recommend attended `/build` instead. Don't launch.

## 2. Preconditions (all mandatory)

- Clean git state, work on a dedicated branch or worktree — recovery from a
  bad run must be "discard the branch", never "untangle the tree".
- Runnable acceptance criteria in the task file (no criteria → no autonomy).
- Quality gates installed (`/gate`) or a bounded goal set (below).
- Permissions scoped: the run can build/test/commit but NOT push or deploy.
  Risk-rate each tool by reversibility and blast radius when scoping the
  allowlist — auto-allow only what discarding the branch fully undoes.
  Be honest about the limit — allowlists gate commands, not the filesystem;
  a worktree isolates the diff, not the machine. For hard isolation use the
  containment ladder in reference.md. Never `bypassPermissions` outside a
  network-isolated container.

## 3. Pick the mechanism (see reference.md for exact commands)

| Situation | Mechanism |
|---|---|
| You stay at the keyboard, same session | `/goal "<criteria> pass, or stop after 20 turns"` |
| Fire-and-forget, this machine | background agent in a worktree, prompted with the /build procedure |
| CI / scripts / scheduled | `claude -p` headless with `--allowedTools`, `--max-turns`, `dontAsk` |
| Exploratory bet, low confidence | slot machine: commit state, timebox one run — accept the result or DISCARD and restart fresh with a better task file; never debug a failed run in place |

## 4. The walk-away contract

Before launching, state: what's running, where (branch/worktree), the gate
that decides success, and the evidence the run must produce (test output,
verifier verdict — claims don't count). Two triggers escalate to a human
instead of pressing on: the same step failing twice (a third attempt in a
degraded context won't do better), and reaching a high-risk
action — push, deploy, data deletion, publishing, spending — which the run
must never take on its own. On completion: PASS → present
evidence and the diff for human review (a human still approves; the agent
does the work). FAIL or gate-capped → report, discard or re-scope, and
restart clean. Correcting a wandering autonomous run in-context is the
known losing move. Either way, if the run exposed a task-file or gate
problem, run /distill so the next launch doesn't repay for it.
