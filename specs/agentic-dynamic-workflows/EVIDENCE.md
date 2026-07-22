# Evidence: instrumented ultracode runs (2026-07-22)

Two live Workflow-tool runs executed from this session specifically to
observe the behaviors this spec replicates. Run ID wf_1d11b4bc-c7b;
7 agents; probe schema {word, n, modelSelfReport}; all agents pinned
`model: 'haiku', effort: 'low'`.

## Run 1 — semantics probe (253,672 total tokens, 24.6s wall)

- **budget object**: `total=null` with no user directive;
  `spent()=8,422` at workflow start — the pool had already accumulated
  the MAIN conversation's output this turn, proving one shared pool;
  `spent()=10,771` after 7 agents → ~2,349 output-scale tokens for the
  whole probe fleet. The unit appears to be output tokens — an
  INFERENCE from one run's deltas, recorded as such; totalTokens
  (253,672) counts full I/O including per-agent system-prompt input.
  Not load-bearing for the design: the agentic meter is independent.
- **Per-agent floor**: ~36,2xx tokens each for trivial one-line
  answers — the subagent bootstrap cost; fan-out is never free.
- **Schema enforcement**: agents with `schema` show
  `lastToolName: "StructuredOutput", toolCalls: 1` — the schema
  becomes a forced tool; validation at the tool layer; `attempt: 1`
  visible (retry counter surfaced per agent). Plain agents: 0 tool
  calls, raw text return.
- **Tier resolution**: `model: 'haiku'` resolved harness-side to
  `claude-haiku-4-5-20251001` in the progress records.
- **Blank contexts**: the Summarize-phase agent replied "I have no
  prior context indicating I've participated in an introspection
  workflow… This is our first exchange" — workflow agents receive
  ONLY the prompt string; phase titles and workflow identity are
  display metadata, invisible to the agent.
- **Concurrency queueing**: par-probe-3 queued at t=0 with its
  siblings but started ~5s later — slot-limited execution visible in
  queuedAt vs startedAt.
- **pipeline() stage callbacks**: pure stage 2 received
  (prevResult, originalItem, index) per item, no barrier.
- **Progress stream fields** (per agent): type, index, label,
  phaseIndex/phaseTitle, agentId, model, state, queuedAt, startedAt,
  attempt, lastToolName/Summary, promptPreview, lastProgressAt,
  tokens, toolCalls, durationMs, resultPreview. Phase events: type,
  index, title. This is the field set RW-V's renderer consumes.

## Journal on disk (transcript dir, journal.jsonl)

Append-only JSONL, interleaved:
`{"type":"started","key":"v2:<sha256>","agentId":"..."}` then
`{"type":"result","key":"v2:<same>","agentId":"...","result":<full
return>}`. Keys are versioned content hashes of the call; `started`
without `result` marks in-flight/crashed work for resume.

## Run 2 — resume probe (108,560 total tokens)

Edited the persisted script: pipeline items `[10, 20] → [10, 21]`
(one mid-script call changed), re-invoked with `resumeFromRunId`.
Observed: the three parallel probes and pipe-s1-10 (all sequenced
BEFORE the edit) replayed `cached: true`, zero tokens, instant. The
changed call ran live. The two calls sequenced AFTER the change
(plain-text probe, summarize) re-ran live DESPITE identical prompts —
**replay validity is prefix-positional, not content-addressed**,
conservative against dataflow between calls. Cache saved 57% of run
cost. `budget.spent()` at resume start had grown again from
main-conversation output between runs (16,985) — shared pool
reconfirmed.

## Sources

- The Workflow tool's own specification (in-harness primary source):
  primitive signatures, caps (min(16, cores−2) concurrency, 1000
  agent lifetime, one nesting level, 4096 items/call), determinism
  bans (Date.now/Math.random), budget contract, resume contract,
  pattern doctrine (adversarial verify, loop-until-dry, judge
  panels), meta/registry format.
- Prior session research: no public documentation of
  ultracode/Workflow exists beyond the harness (verified by web
  sweep, recorded in specs/agentic-core-redesign/EVIDENCE.md's
  external-design-points section).
