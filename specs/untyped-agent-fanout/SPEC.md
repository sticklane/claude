# Close the untyped agent:claude fan-out tier leak

Status: open
Priority: P1
Breakdown-ready: true

## Problem

The 2026-07-11 overnight agentprof window shows $123 flowing through the
`claude` catch-all agent type at fable-5/opus-4-8, including dispatch
chains nested 3–5 deep (`agent:claude > agent:claude > agent:claude`):
~$95 in a home-directory orchestrator session and ~$61 inside a fooszone
/drain run. The catch-all inherits the calling session's model, so an
untyped agent spawning untyped children compounds frontier-tier cost at
every level — the tier ladder inverted, at depth.

This is the same leak class specs/agent-tier-leaks closed for
`general-purpose` ($1,126) and `verifier`: an untyped dispatch inheriting
the session's frontier model where a typed pinned agent (scout /
verifier / implementation-worker) or an explicit cheap-tier override was
called for. The `claude` type — the default when no agent name is given —
was not in that spec's scope. The freehand fan-out doctrine
(.claude/rules/token-discipline.md, "Freehand fan-out") names
`general-purpose` but not the catch-all, and says nothing about *nested*
untyped dispatch, which is what made last night's chains expensive.

Chosen approach (maintainer decision 2026-07-12): trace-and-fix the
dispatch sites + a depth-guard doctrine line (with a hook if feasible) +
a recurring guard metric. Pinning the catch-all type to a fixed tier was
considered and rejected — the catch-all sometimes carries legitimate
judgment work.

## Solution

Rerun the agent-tier-leaks playbook against the `claude` type (trace via
`agent_id` labels, fix the sources), extend the doctrine so untyped
agents don't spawn untyped agents, and add a workboard guard line so a
regression shows up in the weekly numbers instead of the next ad-hoc
audit.

## Requirements

- R1 **Trace the dispatch sites.** The two affected sessions are
  `6fddf102-f06a-4562-bc20-14742aa17582` (home-directory orchestrator)
  and `80161f1c-8c2c-4bc3-a8d5-a4afb10ce3d4` (fooszone /drain). Their
  full sample set is pinned at
  `specs/untyped-agent-fanout/evidence-samples-2026-07-11.jsonl.gz`
  (screened: zero 24+-char hex runs, no home-path strings; regenerate
  with `agentprof claude --since 2026-07-11T18:00:00-05:00` while
  `~/.claude` transcripts still cover the window). Using the pinned
  samples' `agent_id` labels and — where they still exist — the source
  transcripts, identify what dispatched each `agent:claude` chain (skill
  text, freehand orchestrator prompt, FleetView default, or harness
  behavior). Record findings in `specs/untyped-agent-fanout/EVIDENCE.md`:
  per chain, the dispatch site, the depth, the model inherited, and the
  cost. Any further committed profile evidence follows the
  pinned-evidence denylist rule.
- R2 **Fix the sources.** For each R1 site that is toolkit-owned text
  (skill, agent definition, rule, dispatch template), change it to name a
  typed pinned agent or pass an explicit model/effort override. Sites not
  toolkit-owned (harness defaults, one-off human prompts) get a
  documented disposition in EVIDENCE.md instead of a code change.
- R3 **Depth-guard doctrine, hook if feasible.** The "Dispatch authoring"
  section of `.claude/rules/token-discipline.md` gains: an untyped agent
  (catch-all `claude` or bare `general-purpose`) must not spawn another
  untyped agent without an explicit model override — nesting is where
  inheritance compounds. Additionally, IF a PreToolUse hook on Agent
  calls can observe the running agent's own type or depth, ship a
  toolkit hook that warns on violation (never blocks — warn-only, since
  legitimate judgment chains exist), with a runnable test. If the hook
  API cannot see type/depth, record that limitation in one line next to
  the doctrine and ship doctrine-only — the task must not stall on the
  harness.
- R4 **Guard metric.** The cost summary gains an additive
  `untyped_fanout` section: calls and `cost_microusd` through untyped
  agent frames (`agent:claude`, `agent:general-purpose`, with and without
  plugin namespace), split by model, plus a `max_depth` observed for
  untyped-under-untyped chains. Edge rule for depth (also the R3 hook's
  warn condition): count adjacent untyped `agent:` frames in one sample's
  stack, ignoring intervening `wf:`/`stage:`/role markers; a TYPED agent
  frame breaks the chain (`agent:claude > agent:scout > agent:claude`
  is depth 1 twice, not depth 2). Existing sections and field names are
  unchanged (additive only, like the `reprime` section). The
  agent-console workboard cost panel renders one line from it (count +
  cost for the window), omitting it gracefully when the section is
  absent from older summary JSON.

## Out of scope

- Re-pinning the `claude` or `general-purpose` agent types to a fixed
  tier (rejected above).
- Re-auditing the leaks agent-tier-leaks already closed.
- Blocking hooks or any mechanism that kills a dispatch mid-flight.
- Changing drain's dispatch machinery beyond text fixes R2 identifies.

## Acceptance criteria

- [ ] `test -f specs/untyped-agent-fanout/EVIDENCE.md` and it names a
  dispatch site (or explicit "unresolved" disposition) for every
  `agent:claude` chain ≥2 deep in the 2026-07-11 window's two affected
  sessions (R1)
- [ ] Every toolkit-owned site in EVIDENCE.md has a landed text fix
  referenced by commit, or a written no-fix rationale (R2)
- [ ] `sed -n '/## Dispatch authoring/,/^## /p' .claude/rules/token-discipline.md | grep -ci 'untyped'`
  ≥ 1 (word confirmed absent from the whole file at authoring time) —
  placement inside the "Dispatch authoring" section is part of the
  check (R3)
- [ ] If any task's R2/R3 fix edits a `.claude/skills/*` or
  `.claude/agents/*` file, that task's `Touch:` also carries the
  `antigravity/` mirror and a `.claude-plugin/plugin.json` version bump,
  and `claude plugin validate .` passes (per CLAUDE.md's mirror rule;
  conditional because R2's targets are unknown until R1 traces them)
  (R2, R3)
- [ ] Hook path: either the hook script exists with a runnable test
  (violating Agent input → warning emitted; typed or overridden input →
  silent), or the feasibility limitation is recorded beside the doctrine
  line (R3)
- [ ] `cd agentprof && go test ./internal/costsummary/` passes; the
  summary JSON contains `untyped_fanout` with `calls`, `cost_microusd`,
  `by_model`, `max_depth`; no existing field names change (R4)
- [ ] `bash agent-console/scripts/check.sh` passes; the cost panel line
  renders when the section is present and is omitted when absent,
  covered by a renderer test (R4)
- [ ] `bash agentprof/scripts/check.sh` green (R4)

## Open questions

None — the depth edge rule is pinned in R4 (typed frames break the
chain; `wf:`/`stage:`/role markers are transparent), and SCHEMA.md
documents it if the section surfaces there.

## Parallelization

01 = R1 trace (read-only, produces EVIDENCE.md); 02 = R2 fixes (after
01); 03 = R3 doctrine + hook feasibility (independent of 01/02);
04 = R4 summary section + workboard line (independent of 01–03; Touch
disjoint: agentprof/ + agent-console/ vs .claude/ and skills text).

- Group: 03, 04
