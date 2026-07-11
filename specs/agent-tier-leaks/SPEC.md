# Close the agent-tier leaks (verifier on fable, general-purpose sink)

Status: open
Priority: P2

## Problem

agentprof (2026-07-04→11; see ../drain-wake-cost/EVIDENCE.md) shows the
structural tier pins working exactly as designed where they apply — scout
locked to haiku (8,637 calls, $52), implementation-worker locked to opus —
and two paths leaking around them:

1. **Verifier ran $74 of its $187 on fable-5** despite
   `.claude/agents/verifier.md` pinning `model: sonnet`. Likely mechanism
   (identified during spec critique, needs confirmation against the
   transcripts): the plugin cache holds immutable per-version snapshots at
   `~/.claude/plugins/cache/agentic-toolkit/agentic/<version>/`, and the
   0.6.2/0.7.0 snapshots carry `model: inherit` — a session on an old
   plugin version dispatches verifiers at the session's frontier model.
   0.8.3+ (the newest cache snapshot at critique time was 0.8.13) already
   pin `model: sonnet`, so the fix likely shipped; what remains is confirming the leak sessions predate
   0.8.3 and that no other override path (e.g. drain's "one tier up"
   relaunch) contributes.
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
  sites behind the fable-model verifier spend (profile `session` labels →
  transcript lookup, e.g. `go tool pprof -tagfocus session=<id>` against
  the pinned profile at
  ../drain-wake-cost/profile-2026-07-04-to-11.pb.gz; regenerate samples
  with `agentprof claude --since 2026-07-04T00:00:00Z` — the rolling
  `--days 7` window no longer covers the leak sessions). Name the
  mechanism and land ONE of: (a) confirmation the leak is the pre-0.8.3
  `model: inherit` snapshots — then the deliverable is documenting the
  version boundary and the stale-cache mechanism in the verifier agent doc
  or plugin release notes (the cache snapshots themselves are immutable;
  do not edit them); (b) an overriding dispatch path corrected; (c) a
  deliberate escalation (e.g. tier-up retry) written into the verifier
  agent docs as policy.
- R2 **Tier-dispatch doctrine for freehand fan-outs.** One short block in
  `.claude/rules/token-discipline.md` (the doctrine home the skills already
  cite; CLAUDE.md gets at most a pointer line, per the repo's
  cite-don't-restate convention): mechanical fan-out work dispatched
  outside a skill uses the typed pinned agents
  (scout/verifier/implementation-worker) or passes an explicit cheap-tier
  `model` override to general-purpose; bare general-purpose at session
  model is reserved for judgment work. Cite the measured $/call inversion
  (general-purpose $0.067 vs pinned worker $0.057).
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

- [ ] Fable-model verifier mechanism named with transcript evidence from the pinned window, and the matching R1 outcome landed (version-boundary documentation, dispatch-site fix, or escalation policy) (R1)
- [ ] `grep -q '0\.067' /Users/sjaconette/claude/.claude/rules/token-discipline.md` (the file already contains an unrelated "general-purpose" mention, so grep the new block's cited $/call figure instead) AND MANUAL: the block names the pinned agents as the default for mechanical fan-outs and reserves session-model general-purpose for judgment work (R2)
- [ ] Namespace explanation present in agentprof docs (`grep -riqE 'agentic:' /Users/sjaconette/claude/agentprof/README.md /Users/sjaconette/claude/agentprof/SCHEMA.md` hits) AND MANUAL: the hit explains the bare-vs-prefixed split (R3)
- [ ] Any stale shadow agent copies found under R3 are deleted; if any `.claude/agents/*.md` file is edited — under ANY requirement, including an R1 outcome documented in verifier.md — the antigravity mirror + `.claude-plugin/plugin.json` bump ship in the same commit and `claude plugin validate .` passes (cross-cutting: /breakdown should assign this to one closing task with the union Touch) (R1, R3)
- [ ] MANUAL (deferred, needs a week of runs): next 7-day profile shows verifier spend ≥90% on sonnet (absent documented escalations) and a falling general-purpose $/call

## Open questions

- (Resolved during critique) The plugin sources agent definitions from this
  repo's `.claude/agents/` (`plugin.json` enumerates them; marketplace
  source is `./`); the installed dispatch path uses immutable per-version
  cache snapshots under `~/.claude/plugins/cache/agentic-toolkit/agentic/`,
  so "drift" = version skew between snapshots, never a separate editable
  dir. R1's fix is documentation or a forward version bump, never a cache
  edit.
