# agentprof: attribution gaps and profile hygiene

Status: open
Priority: P2
Breakdown-ready: true

## Problem

Five attribution/hygiene defects in `agentprof claude` output, all
measured in the 2026-06-27→07-11 window (EVIDENCE.md):

1. **Typed slash commands lose skill attribution — $1,962, half of all
   slash-turn spend.** `normalizeSkillFrame()`
   (`internal/claude/claude.go:465`) reads only the transcript's
   `attributionSkill` field, which the harness sets on the Skill-tool
   invocation path but not when the user types `/drain …` directly (the
   command arrives as a `<command-name>` tag in the user message).
   `turnPrompt()` (claude.go:~647) already extracts the command name from
   those tags — but only to name the turn frame, never the skill frame.
   /drain alone had $216 unattributed vs $134 attributed; /idea $353
   unattributed. (The native attributionSkill design stays — this is a
   fallback for the typed path, not a re-spec.)
2. **Project frames are polluted.** The home directory appears as project
   `sjaconette` ($3,862 — the single biggest "project"), ~30 `mktemp`
   dirs appear as `tmp.XXXX` rows (~$35 combined), and at least one agent
   sidecar transcript directory appears as a project
   (`agent-a571c48f410951a76`, $0.90) — the latter a straight parsing
   bug: agent transcripts should fold into their owning session's
   project, or be dropped, never minted as projects.
3. **`tool:(pending)` noise: 8,854 samples (9.4% of the file) with empty
   `values{}`.** Emitted one per tool_use with no matched tool_result
   (`toolSamples()`, claude.go:~857). ~30 per session is far more than
   plausible user interruptions — likely unmatched result shapes (Agent
   tool results arriving as task-notifications, TaskOutput). Value-less
   samples bloat the JSONL and put a dead frame in every flame graph.
4. **No "no model" bucket in the cost summary.** `modelLeaf()`
   (`internal/costsummary/costsummary.go:~100`) walks past `tool:`/marker
   frames, so every main-loop tool-duration sample lands in
   `by_model["main"]` — 30.8h of duration booked to a "model" named
   `main` (documented as a known wart in
   specs/workboard-weekly-cost-view/tasks/05; the fix was deferred).
   `<synthetic>` rows (59 calls, 0 tokens) also sit undifferentiated in
   by_model.
5. **No per-agent-instance identity.** Samples carry only
   `session/source/turn` labels, so five parallel scouts in one turn are
   indistinguishable — fan-out width and per-instance parallelism cannot
   be measured (an analysis this week initially mis-read /breakdown as
   sequential because of this). The agent sidecar transcript id exists at
   parse time and is currently discarded.

Plus one forward-looking guard: profiles embed every skill/turn frame
string verbatim. A retired private-skill codename appeared as a frame in
this window's output — harmless locally, but any profile artifact pinned
into a repo as evidence (the drain-wake-cost precedent) would republish
it. agentprof already scrubs credential-shaped strings from turn frames;
frame-name scrubbing needs the same treatment with a user-supplied local
denylist (never committed).

## Solution

Six additive fixes in `internal/claude` + `internal/costsummary`: a
command-name fallback for the skill frame, project normalization (home →
`(home)`, mktemp → `(tmp)`, agent-dirs folded), pending-sample
consolidation, an explicit `(tools)` leaf bucket in by_model, an
`agent_id` label on subagent samples, and an optional frame-denylist file
applied to every emitted frame at sample-emit time (see R6).

## Requirements

- R1 **Slash-command skill fallback.** When `attributionSkill` is empty
  and the turn's opening user message carries a `<command-name>/x</command-name>`
  tag, emit `skill:x` (plugin-namespace stripped, same normalization as
  today). Harness-builtin commands that are not skills (`/clear`,
  `/model`, `/reload-plugins`) map to `(no skill)` via a small builtin
  denylist. attributionSkill, when present, always wins.
- R2 **Project normalization.** The user's home directory transcript dir
  maps to project `(home)`; directories matching mktemp shapes
  (`tmp.[A-Za-z0-9]{10}` and the like) map to `(tmp)`; agent sidecar
  transcript dirs (`agent-<hex>`) are folded into their owning session's
  project when resolvable, else dropped with a parse-stat counter — never
  emitted as projects. Home detection is injectable (parameter or env
  override consulted before `os.UserHomeDir()`) so fixtures can pin it —
  the test must be hermetic on any machine.
- R3 **Pending-sample consolidation.** tool_use blocks with no matched
  result no longer emit one empty-valued sample each; they aggregate into
  a `pending_calls` value on a single per-turn `tool:(pending)` sample
  (or are dropped under a flag). A parse-stat logs the count so
  result-matching regressions stay visible. Investigate and fix the two
  known unmatched shapes (Agent-tool/TaskOutput results) if they account
  for the volume.
  - **Maintainer decision 2026-07-13 (task 09) — the ≥8% total-sample
    drop is struck; empty-values=0 stands.** Re-measured against real
    `~/.claude` on the 14-day window (evidence/09-r3-remeasure.md): current
    parser 131,519 samples vs b4971fe 131,521 — a **0.0015%** drop, not
    ≥8%. Empty-valued `tool:(pending)` samples = **0** (all 4 residual
    pending samples carry `pending_calls`). The ≥8% projection assumed the
    8.87%-of-total pending samples would be eliminated; instead the tasks
    03/08 Agent-tool/TaskOutput match fixes re-attribute them to their real
    tool frames sample-count-neutrally (one sample either way), and
    consolidation only collapses same-turn multiples (4 residual unmatched
    calls, each in its own turn → 4→4, zero net removal). The parser is
    correct as-is — eliminating those samples would lose the attribution
    tasks 03/08 recover — so no parser change is made.
- R4 **`(tools)` and `(synthetic)` buckets in by_model.** `modelLeaf()`
  returns a sentinel for samples with no model frame; the summary shows
  them as `(tools)` (duration-only) — `main` never appears as a model
  key. `<synthetic>` keeps its own row but is excluded from `calls`
  aggregation or explicitly labeled; pick one and document it.
- R5 **Agent-instance label.** Samples parsed from an agent sidecar
  transcript carry label `agent_id=<sidecar id>`. Existing labels
  unchanged; SCHEMA.md documents it (enables fan-out width and true
  parallelism measurement, and `-tagfocus agent_id=…`).
- R6 **Frame denylist scrub.** If `~/.config/agentprof/frame-denylist`
  (one string per line; override via `--frame-denylist`) exists, any
  frame containing a listed string is replaced by `(redacted)` — applied
  to EVERY emitted frame string (project, turn, skill, agent, role/stage
  markers, model) at sample-emit time. NOTE: the existing secret scrub
  (`internal/claude/scrub.go`) touches only turn-prompt text and reply
  heads — skill frames flow from `normalizeSkillFrame()` unscrubbed, and
  the skill frame is the documented leak vector, so hooking only the
  existing scrub site does NOT satisfy this requirement. The denylist
  file itself stays local-only; the repo ships only the mechanism. README
  documents it and adds the repo rule: evidence profiles pinned under
  specs/ must be generated with the denylist active.

## Out of scope

- Harness changes (setting attributionSkill on the typed path upstream).
- Re-speccing native attributionSkill or workflow linkage (both shipped).
- The bare-vs-namespaced agent frame split (documented via
  specs/agent-tier-leaks R3).
- Backfilling old merge caches / saved summaries.

## Acceptance criteria

- [ ] Testdata fixture: a turn whose first user message is a
      `<command-name>/parallel</command-name>` tag and no attributionSkill
      yields `skill:parallel` frames; a `/clear` turn yields `(no skill)`;
      an attributionSkill-carrying line still wins over the tag (R1)
- [ ] Testdata fixtures: home-dir project maps to `(home)`, `tmp.*` to
      `(tmp)`, and an `agent-*` sidecar dir emits no project of its own (R2)
- [ ] On the full local 14-day window, `tool:(pending)`-frame samples
      with empty values number 0 vs the pre-change parser (spot-check
      figure recorded in evidence/09-r3-remeasure.md) (R3). The original
      "total sample count drops ≥8%" clause is STRUCK by maintainer
      decision 2026-07-13 (task 09) — re-measurement showed a 0.0015% drop,
      not ≥8%, because the tasks 03/08 match fixes re-attribute pending
      calls sample-count-neutrally rather than eliminating them; see the R3
      requirement note and evidence/09-r3-remeasure.md.
- [ ] `--summary` by_model contains no `main` key on a fixture containing
      main-loop tool-duration samples; `(tools)` holds their duration; AND
      the agent-console workboard cost panel is checked for special-casing of
      the literal `main` key (expected: it iterates by_model keys generically
      — record the check in evidence/, fix the panel if not) (R4)
- [ ] Samples from an agent sidecar fixture carry `agent_id`, and
      `grep -qi 'agent_id' agentprof/SCHEMA.md` (R5)
- [ ] With a denylist file listing a substring of a fixture SKILL name,
      emitted JSONL contains `(redacted)` where the `skill:` frame was and
      the substring appears nowhere in the output (also exercise a project
      frame match); `grep -qi 'denylist' agentprof/README.md` (R6)
- [ ] `bash agentprof/scripts/check.sh` green (all)

## Open questions

- R2: fold agent-dir samples into the owning project requires resolving
  the sidecar→session mapping at directory-scan time; if not cheaply
  resolvable, dropping with a counter is acceptable v1.
- R3: whether to keep a `--keep-pending` escape hatch for debugging
  result-matching. Default: yes, flag-gated.

## Parallelization

Task map: 01 (R1) → 02 (R2) → 03 (R3) → 04 (R5) are a SERIAL chain — all
edit `internal/claude/claude.go` emission paths; do NOT drain in
parallel. 05 (R4) is costsummary-only, disjoint from the parser chain,
parallel-safe with its head. 06 (R6) runs last (wraps the emit path all
others feed). Format grammar per specs/drain-rolling-window/SPEC.md's
Parallelization section.

- Group: 01, 05
