# Decision record: orchestrator context self-management (drain baton)

Date: 2026-07-03 (amended 2026-07-03 — see cross-vendor note below)
Spec: [`specs/orchestrator-context/SPEC.md`](../../specs/orchestrator-context/SPEC.md)
Research: [`docs/context-management-research-2026-07.md`](../context-management-research-2026-07.md)

## Context

Drain's queue state survives session death (committed `Status:` flips), but the
orchestrator _session itself_ only degrades — its sole prior guidance was "if
this session grows heavy, tell the user to `/clear` and re-run `/drain`":
manual, and dependent on a human noticing. The research confirms the failure
mode is real and gradual ("context rot": recall degrades before the hard
limit) and that compaction alone is insufficient for multi-context-window
work. The prescribed remedy is deliberate harness artifacts plus fresh-session
relaunch, each fresh instance following a read-state-then-verify ritual.

## Decision

Give each orchestrator (drain, build, parallel, and the ultra-mode
workflow templates) a **baton-pass step** at every safe boundary (a task
verdict recorded and committed): evaluate the trigger, and when it fires write
a mini-handoff (`specs/<slug>/DRAIN-BATON.md`), spawn a fresh detached
generation of itself, report the pass, and end the turn. State never lives only
in context — the baton is small because task files already checkpoint the
queue.

### Trigger: generation budget (N=4) + degradation override

- **Deterministic generation budget** — hand off after **N recorded verdicts**
  in one session. Default **N=4**, overridable per-spec via a `Relaunch-every:
N` header in the drained spec's SPEC.md header block (documented in
  breakdown's queue conventions; absence means 4).
- **Degradation override** — hand off early at the next boundary if the
  orchestrator notices itself re-reading files it already read, losing queue
  position, repeated failed corrections, or a compaction event. Proactive,
  never failure-triggered: degradation is a gradient, so hand off _before_
  limits.

### Cap: max-generations = 10

A **max-generations cap of 10** prevents runaway relaunch loops. Hitting it
stops with the baton written and a needs-attention note instead of respawning.

### Fresh-instance ritual (read state, then verify)

Generation G+1's first acts: (1) read the baton, (2) read task-file `Status:`
lines, (3) `git log --oneline -15`, (4) run one cheap verification (the
project check or the last-flipped task's acceptance command) to catch
undocumented drift — only then dispatch. On draining the whole queue, the final
generation deletes the baton file.

## Research basis

The mechanism is grounded in `docs/context-management-research-2026-07.md`.
Anthropic sources were 3-vote verified: **context rot** (recall degrades before
the hard context limit), **compaction is insufficient** for work spanning
multiple context windows, and the **read-state-then-verify** ritual for each
fresh instance.

### Cross-vendor corroboration (Anthropic + OpenAI + Google)

Per the **2026-07-03 amendment** to the spec, the cross-vendor calibration leg
that was originally an open caveat has since verified (research doc, "Follow-up
findings (2026-07-03)"). This decision records **cross-vendor corroboration**,
superseding the earlier, now-stale "Anthropic-only" vendor-coverage caveat:

- **Anthropic** — context rot, insufficient-compaction, read-state-then-verify
  (3-vote verified).
- **OpenAI** — the explicit criterion "trim/clear when turns are independent,
  summarize only when decisions / IDs / constraints must survive" directly
  corroborates relaunching at task boundaries: drain's decisions live in
  committed task files, not in conversation context, so a fresh generation
  loses nothing load-bearing.
- **Google** — corroborates the same boundary-relaunch remedy (research doc
  follow-up findings).

No mechanism change followed from the cross-vendor verification — it converts a
caveat into corroboration.

### Remaining gap (leg-B Anthropic re-verification)

The one open item is the **leg-B Anthropic re-verification** set, still
unverified after two attempts. It does not block this decision (the trigger,
mechanism, scope, and cap were decided in the 2026-07-03 interview); revisit if
those items verify later.

## Links

- Spec: [`specs/orchestrator-context/SPEC.md`](../../specs/orchestrator-context/SPEC.md)
- Research: [`docs/context-management-research-2026-07.md`](../context-management-research-2026-07.md)
- Fixture e2e evidence: [`specs/orchestrator-context/evidence/05-e2e.md`](../../specs/orchestrator-context/evidence/05-e2e.md)
