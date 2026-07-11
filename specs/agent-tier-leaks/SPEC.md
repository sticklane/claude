# Close the agent-tier leaks (verifier on fable, general-purpose sink)

Status: open
Priority: P2

## Problem

agentprof (2026-07-04→11; see ../drain-wake-cost/EVIDENCE.md) shows the
structural tier pins working exactly as designed where they apply — scout
locked to haiku (8,637 calls, $52), implementation-worker locked to opus —
and two paths leaking around them:

1. **Verifier ran $74 of its $187 on fable-5** despite
   `.claude/agents/verifier.md` pinning `model: sonnet`. Possible sources:
   the plugin-served agent definition differing from the repo-local one, a
   dispatch path passing an explicit model override (e.g. drain's
   "one tier up" relaunch, or /build sessions overriding), or verifier-role
   work dispatched through a different agent type. Unconfirmed.
2. **general-purpose is the second-largest sink overall**: $1,126 across
   16,771 calls at $0.067/call — costlier per call than the opus-pinned
   implementation-worker — because it inherits the calling session's
   frontier model ($474 on fable). It is the default vehicle for freehand/
   ultracode fan-outs, i.e. exactly the mechanical work the tier ladder
   exists for.

Also unconfirmed: profiles show both bare (`agent:verifier`) and prefixed
(`agent:agentic:verifier`) frames. Hypothesis: bare = repo-local
`.claude/agents/` in this dev checkout, prefixed = plugin-served. If true
it's an attribution nuance to document, not a defect; if false, something
is dispatching stale agent copies.

## Solution

Trace each leak to its dispatch site using the transcripts (the profile's
`session` labels identify which sessions produced fable-model verifier and
general-purpose samples), fix the source — aligning plugin agent
definitions with the repo pins, and adding a short tier-dispatch doctrine
where freehand orchestration reaches for general-purpose — and record the
namespace finding in agentprof's docs.

## Requirements

- R1 **Verifier leak traced and closed.** Identify the sessions/dispatch
  sites behind the fable-model verifier spend (profile labels → transcript
  lookup), name the mechanism, and fix it: plugin definition aligned to
  `model: sonnet`, or the overriding dispatch path corrected, or — if the
  override is deliberate (e.g. escalation retry) — the escalation rule
  written into the verifier agent docs so it's a policy, not a leak.
- R2 **Tier-dispatch doctrine for freehand fan-outs.** One short block in
  this repo's CLAUDE.md (or the doctrine doc the skills already cite):
  mechanical fan-out work dispatched outside a skill uses the typed pinned
  agents (scout/verifier/implementation-worker) or passes an explicit
  cheap-tier `model` override to general-purpose; bare general-purpose at
  session model is reserved for judgment work. Cite the measured $/call
  inversion (general-purpose $0.067 vs pinned worker $0.057).
- R3 **Namespace finding verified and documented.** Confirm or refute the
  bare-vs-prefixed hypothesis against transcripts (which project dirs
  produced bare frames, and do they carry repo-local `.claude/agents/`
  definitions?). Record the answer in agentprof's README or SCHEMA notes so
  future profile readers interpret the split correctly. If any bare frame
  turns out to be a stale shadow copy of a plugin agent, delete the copy
  (per the no-shadow-copies rule).

## Out of scope

- Changing any pinned tier itself (scout=haiku, worker=opus,
  verifier=sonnet, critic=opus stay as-is).
- Workflow-subagent model policy (Workflow scripts pass per-call model/
  effort; that's the workflow author's lever).
- Harness changes to general-purpose's model inheritance.
- Orchestrator/session model choice (covered as doctrine in
  specs/drain-wake-cost R6).

## Acceptance criteria

- [ ] Fable-model verifier mechanism named with transcript evidence, and the corresponding fix landed (plugin def, dispatch site, or documented escalation policy) (R1)
- [ ] `grep -qiE 'general-purpose' /Users/sjaconette/claude/CLAUDE.md || grep -riqE 'general-purpose' /Users/sjaconette/claude/.claude/docs/` — tier-dispatch doctrine present and it names the pinned agents as the default for mechanical fan-outs (R2)
- [ ] Namespace explanation present in agentprof docs (`grep -riqE 'agentic:' /Users/sjaconette/claude/agentprof/README.md /Users/sjaconette/claude/agentprof/SCHEMA.md` returns a hit in a bare-vs-prefixed context) (R3)
- [ ] Any stale shadow agent copies found under R3 are deleted (R3)
- [ ] MANUAL (deferred, needs a week of runs): next 7-day profile shows verifier spend ≥90% on sonnet (absent documented escalations) and a falling general-purpose $/call

## Open questions

- Does the plugin build/packaging step source agent definitions from this
  repo's `.claude/agents/` verbatim, or from a separate plugin dir that can
  drift? Answer determines whether R1's fix is a sync step or a one-off
  edit.
