# 2026-07-21 — drain gen-1 baton pass spawned a detached headless successor from an attended session

## What happened

An attended `/drain` run in `portfolio-tracker` (session
`263ced16-4e84-4910-99be-8286826c0c14`, gen 1, W=1) hit the baton-pass
verdict threshold (`max(2, 6 − W)` = 5 recorded verdicts) after critique
intake → auto-breakdown → tasks 01–04 all DONE/merged. Instead of offering
the baton to the human at the keyboard, the hub wrote `DRAIN-BATON.md` and
spawned generation 2 as a **detached headless process**
(`nohup claude -p "/drain (generation 2, …)" … --model opus &`, pid 47310) —
an unsupervised background session the human only discovered afterward
("why did we start this as a separate process").

The full session transcript is retained locally outside the repo (it embeds
personal session context, so it is not published; a later foreground turn may
be absent — the copy was snapshotted mid-session).

## Why the model chose the detached path

The drain skill text is ambiguous about attended gen-1 hand-offs:

- SKILL.md step 3a: "spawn the successor generation (**awaited where a
  parent can supervise; else headless**), report the pass, and end your
  turn at once" — and separately: "**Gen 1 is always attended**; passing
  `attended` makes every trigger OFFER the baton + relaunch command instead
  of self-relaunching."
- reference.md "Baton pass": "awaited where an attended parent can
  supervise, via the detached headless command below only where none can",
  followed by a fully-specified, fixture-tested `nohup` relaunch template —
  the only concrete mechanism given.

The hub read "passing `attended`" as an explicit launch argument (not
passed), so the OFFER branch was skipped. For the self-relaunch it judged
the "awaited" branch unsafe — an awaited successor is a subagent, and the
reference only *verifies* background `Task` dispatch for headless `claude
-p` sessions, not nested Agent-tool dispatch from a subagent — and fell
through to the only mechanically-specified path: the detached `nohup`
template. Locally-consistent reasoning, wrong outcome for an attended
session.

## Why it matters

- A detached successor is invisible to the attended session's harness: no
  fleet/agent tracking, no completion notification, quota consumption the
  human can't see, and no way for the human's live session to steer it.
- The attended human explicitly present at gen 1 is the cheapest possible
  supervisor; "Gen 1 is always attended" reads like it was *meant* to route
  gen-1 triggers to the OFFER branch, but the "passing `attended`" clause
  makes that conditional on an argument nobody passes.
- The fixture-tested `nohup` template is the path of least resistance:
  whenever the awaited-vs-headless judgment call is uncertain, the concrete
  template wins, so the ambiguity systematically resolves to detached.

## Follow-up (tracked in docs/TASKS.md)

Disambiguate drain's baton-pass semantics for attended gen-1 sessions:
either make gen 1 unconditionally OFFER (the "Gen 1 is always attended"
reading), or specify the awaited-successor mechanism as concretely as the
nohup template so the supervised path is actually takeable. Also state
whether a detached successor should ever be spawned while a human is at the
keyboard without an explicit opt-in.
