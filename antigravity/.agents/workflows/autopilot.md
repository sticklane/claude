---
description: Launch a task for low-supervision execution with verification guardrails - classify it, set the guardrails, then run hands-off. For walking away from well-specified, peripheral work.
---

Run the task file given after the command with minimal supervision.
Autonomy is earned by verification, not granted by optimism.

**Startup session sweep (advisory).** Before classifying, check whether
another live session's working directory is this same repo — the Agent
Manager's session list, or whatever runtime session record is available;
unavailable → one "sweep unavailable" line and continue. Print one line
per foreign live session found; never blocking (concurrent-sessions rule,
folded into AGENTS.md, cited not restated).

1. **Classify (go/no-go).** Low-supervision execution fits: peripheral
   features, prototypes, mechanical migrations — anything with runnable
   acceptance criteria and no irreversible actions. Core business logic and
   security-sensitive code don't disqualify a task — they raise the bar it
   must clear first: tighten acceptance criteria to runnable commands and
   confirm worktree isolation, then launch. What genuinely doesn't fit is an
   ambiguous spec — that's an unresolved spec question, not a task needing a
   human to watch a build. Say so, file it as a HUMAN.md `ask`/`decide`
   entry (or route it back through the spec pipeline), and don't launch.

2. **Preconditions (all mandatory).**
   - Clean git state; dedicated branch or worktree — recovery must be
     "discard the branch", never "untangle the tree".
   - Runnable acceptance criteria in the task file (no criteria → no
     autonomy).
   - Gates installed (/gate hooks) so edits are checked deterministically,
     OR, when gates aren't installed, a **bounded goal** set instead:
     staying at the keyboard in this conversation (step 3's "This
     conversation" launch shape) with an explicit stop condition stated up
     front — "<criteria> pass, or stop after ~20 turns".
   - Terminal Execution Policy: deny list covers pushing to the remote
     (e.g., under git: `git push`), deploys, and
     destructive commands (Settings → Antigravity → Terminal Execution
     Policy). Risk-rate each tool by reversibility and blast radius when
     scoping the policy — auto-allow only what discarding the branch fully
     undoes. Turbo mode ONLY with the deny list in place; never disable
     review policies for core work.

3. **Launch shape.** Confirm with the user, then either:
   - This conversation: proceed hands-off through /build with artifact
     review policy relaxed ("Always Proceed") — appropriate only because
     step 1 classified the task as peripheral; or
   - Background: a separate Agent Manager agent (or scheduled task) on the
     worktree with the drain workflow's step-2 worker prompt — including
     its resolved build-workflow path and its over-budget stop (the worker
     stops with verdict BLOCKED "over budget" when remaining work clearly
     exceeds the task's `Budget:`). Note:
     scheduled tasks run on a Flash-class model — fine for mechanical
     tasks, wrong for judgment-heavy ones.
   - Timebox exploratory bets (the slot machine): one run; accept the
     result or DISCARD the branch and restart fresh with a better task
     file. Never debug a failed autonomous run in place.

4. **The walk-away contract.** Before launching, state: what's running,
   where (branch/worktree), the gate that decides success, and the evidence
   the run must produce (acceptance-command output in the walkthrough —
   claims don't count). The run reports back only that **verdict + evidence**,
   never its transcript. Two triggers escalate to a human instead of
   pressing on: the same step failing twice (a third attempt in a degraded
   context won't do better), and reaching a high-risk action —
   push, deploy, data deletion, publishing, spending — which the run must
   never take on its own. On completion: PASS → present evidence and the diff
   for human review (a human still approves). FAIL → report, discard or
   re-scope, relaunch clean. Either way, if the run exposed a task-file or
   gate problem, apply the distill skill so the next launch doesn't repay
   for it.

   **Exit checklist (fixed final message).** At scope exhaustion the run's
   final message is a three-section **checklist**, one file path per entry,
   carrying only what autopilot produces: (1) **defaults taken** — the
   reversible-default decisions logged to the task file's `## Decisions`,
   which the build workflow this run dispatches already produces, so
   autopilot reads that section rather than editing it; (2) **the task's
   blocker**, if any, with what unblocks it; and (3) **the next command**.
   "Nothing needs you" is a valid checklist. This is autopilot's
   three-section analogue of the drain workflow's six-section exit checklist
   (cite drain, don't restate its sections).

5. **Pre-cap baton (long runs).** The turn budget terminates the run — there
   is no "after the cap". At the last committed task verdict BEFORE ~80% of
   the budget, write drain's baton artifact (`DRAIN-BATON.md`: done/next log,
   generation number, in-flight/unmerged state), judging advancement by new
   commits since launch — no new commits since the previous baton → stop for
   spec repair, don't hand off. Then STOP: an Antigravity run cannot
   self-relaunch claude, so it writes the baton and stops for the human to
   relaunch. Same baton grammar and generations cap as the drain workflow.
