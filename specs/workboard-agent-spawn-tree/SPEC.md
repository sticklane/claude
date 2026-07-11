# workboard: agent spawn-tree visualization

Status: open
Priority: P2

## Problem

`workboard` (`.claude/skills/workboard/workboard.py`) is the live, cross-repo
dashboard of open work — specs, tasks, handoffs, and every Claude Code
session (active/recent/idle/stale). Its session view today is a flat,
metadata-only row per session: id, cwd, branch, first prompt, timestamps,
state (`scan_sessions()`, workboard.py:788-838, fed by
`_first_prompt_and_meta()` at workboard.py:606-641 and `_last_record_ts()`
at workboard.py:665-684). It never parses `tool_use`/`tool_result` events,
so a session that spawned a dozen nested sub-agents renders identically to
one that spawned none — there is no way to see, across the machine's whole
work history, which agents ran under which session, or which sub-agents a
worker itself spawned.

`/fleet` (`.claude/skills/fleet/`) covers a narrower, adjacent need: a
static HTML snapshot of the CURRENT session's own agents, discovered via
the harness TaskList tool and `git worktree list`, rendered as a flat list
(status tiles + Gantt timeline + table). It explicitly scopes out
historical/cross-session data to workboard (workboard/SKILL.md:3,8). Fleet
has no parent-child rendering either, and its discovery mechanism (TaskList,
worktrees) has no visibility into sessions from other repos or past
sessions in this one.

Neither skill can currently answer "show me the tree of agents this
session spawned, including any sub-agent that itself spawned further
sub-agents" — for any session, live or historical.

## Solution

Extend workboard's existing live, modular architecture rather than build a
new adjacent skill:

1. **Data layer**: add `extract_agent_tree(session_jsonl_path)` to
   workboard.py. It parses the parent session's `.jsonl` for Agent/Task
   `tool_use` events (capturing the returned `agentId`) and their
   `tool_result` pairs, then for each `agentId` loads the sub-agent's own
   transcript pair at
   `~/.claude/projects/<proj>/<sessionId>/subagents/agent-<agentId>.jsonl`
   plus its sibling `agent-<agentId>.meta.json`. The meta file carries
   `agentType`, `description`, `toolUseId` (links back to the parent's
   `tool_use` call), and `spawnDepth`; each event inside the sub-agent's own
   `.jsonl` carries a `sessionId` back-reference. The function recurses into
   any Agent `tool_use` events found inside a sub-agent's own transcript,
   confirmed on this machine to reach `spawnDepth: 2` (a sub-agent spawning
   its own sub-agent) — so the recursion is not hypothetical, real
   multi-level trees exist in current transcripts.
2. **Wiring**: add a sibling `scan_session_spawns()` function (matching the
   existing `scan_*()` pattern that feeds `assemble()` at workboard.py:1424)
   that runs `extract_agent_tree()` per session and attaches the resulting
   tree to that session's existing record.
3. **Rendering**: extend the existing session view (near
   `_session_timeline_html()`, workboard.py:1762-1784) with a per-session
   expandable node showing an indented collapsible tree — one row per
   agent, indented by `spawnDepth`, each row collapsible/expandable,
   showing agent type/description, status (running/completed/failed —
   reusing `/fleet`'s existing status-chip convention: glyph + word, never
   color alone), and start/elapsed time. Failed or errored sub-agent
   branches get distinct styling (status chip + a visually distinct row
   treatment) so a broken branch is visible without expanding every node.
4. **Live model preserved**: the tree is computed by `scan_session_spawns()`
   on every request, same as every other workboard `scan_*()` — no new
   snapshot/export mechanism, no polling or websocket layer.
5. **Antigravity mirror**: workboard currently has no antigravity mirror
   (confirmed absent from `antigravity/skills/` during scouting for this
   spec) — this is real repo drift from CLAUDE.md's mirroring convention
   ("`.claude/` is the source of truth; `antigravity/` is a mirrored
   port... when a skill changes here, mirror the change there in the same
   commit"), independent of this feature. Closing this spec's implementation
   must not widen that gap: the closing task's `Touch:` list must include
   creating/updating the antigravity mirror for workboard (or, if that
   mirror genuinely does not exist yet, note it as a pre-existing gap this
   spec does not fix and file it separately) — see `## Out of scope` below.

## Design decisions (resolved by inference, not by asking)

These four questions were flagged when this spec was commissioned;
research during scouting resolved all four without needing to interrupt
the user:

- **(a) Historical scope**: sessions in scope include recent/idle/stale,
  not just the live current one. This matches workboard's existing
  cross-session categorization — it's workboard's whole reason to exist
  next to `/fleet`, which is explicitly current-session-only.
- **(b) Shape — tree vs. flat list**: a genuine multi-level parent→child
  spawn tree is correct and, critically, buildable: Claude Code's
  transcript format does capture real parent-child linkage via
  `subagents/agent-<agentId>.{jsonl,meta.json}` (fields: `agentId`,
  `agentType`, `toolUseId`, `spawnDepth`, and a `sessionId` back-reference
  inside each sub-agent event) — confirmed by inspecting real transcripts
  on this machine, including one reaching `spawnDepth: 2`. This is not a
  hard blocker; neither workboard nor fleet parses this today.
- **(c) Live vs. point-in-time**: extend workboard's existing
  re-scan-on-every-request server model. `/fleet`'s static HTML snapshot is
  a deliberately different, already-shipped mechanism for a different
  scope (current session only) and is not reused here.
- **(d) Extend workboard vs. new skill**: extend workboard directly. Its
  `scan_*()` → `assemble()` architecture is designed for exactly this kind
  of addition, and a new adjacent skill would duplicate the
  workboard/fleet scope split this repo already documents.

## Requirements

- R1: `extract_agent_tree(session_jsonl_path)` returns a tree structure
  (nested dict or dataclass) representing every Agent tool_use spawned
  directly by the session, and recursively every Agent tool_use spawned by
  each of those sub-agents, using `agentId`/`toolUseId`/`spawnDepth` from
  the `subagents/agent-<agentId>.meta.json` files.
- R2: Each tree node carries at minimum: `agentId`, `agentType`,
  `description`, `status` (running/completed/failed — derived the same way
  fleet derives status today), `spawnDepth`, `started_ts`, `ended_ts` (if
  available).
- R3: A session with zero Agent tool_use events produces an empty tree
  (not an error) — the existing flat-row rendering is unaffected for such
  sessions.
- R4: A session whose sub-agent itself spawned a further sub-agent (i.e. a
  real `spawnDepth: 2`+ case) renders that grandchild nested under its
  parent agent, not flattened to the session's top level.
- R5: `scan_session_spawns()` follows the existing `scan_*()` contract
  (workboard/reference.md:62-67: return dicts keyed with
  `last_touched`/`last_ts`) and is wired into `assemble()` without changing
  any other scan function's output shape.
- R6: The rendered session view shows an expandable/collapsible tree
  per session with a spawn tree; sessions without one render exactly as
  today (no visual regression for the common case).
- R7: Failed/errored sub-agent branches are visually distinguishable from
  completed ones (status chip, consistent with `/fleet`'s existing
  glyph+word convention — never color alone).
- R8: `workboard.py --json` output includes the new tree data per session
  (so the data layer is independently testable without rendering).

## Out of scope

- Building or backfilling the antigravity mirror for workboard as a whole,
  if it turns out to be a pre-existing gap unrelated to this feature (only
  the incremental mirror of whatever this spec adds is in scope, per
  CLAUDE.md's mirroring convention).
- Real-time push-updating (websockets, SSE) — the live model here means
  "re-scans on refresh," identical to every other workboard `scan_*()`,
  not a new streaming mechanism.
- A graphical DAG renderer (reusing `_shared/viz.py`'s `dag()`) for this
  view — the collapsible indented tree is the v1 shape; a DAG view is a
  possible future enhancement, not part of this spec.
- Capturing or displaying anything beyond what's already in `subagents/`
  transcripts and their meta.json files (e.g., no new logging/instrumentation
  is added to the harness itself).
- Cross-machine or cross-user aggregation — scope stays this machine's
  `~/.claude/projects/` tree, matching workboard's existing scope.
- Any bound tighter than workboard's existing active/recent/idle/stale
  session window — v1 does not add a new retention cap; if scanning every
  session's `subagents/` directory proves too slow in practice, that's a
  follow-up perf task, not blocking this spec.

## Acceptance criteria

- [ ] `python3 .claude/skills/workboard/workboard.py --json` on a repo with
      at least one session that spawned sub-agents includes a
      `spawn_tree` (or equivalently named) field per session, non-empty
      for that session.
- [ ] A unit test for `extract_agent_tree()` against a fixture session
      `.jsonl` + `subagents/` directory (constructed to include a
      `spawnDepth: 2` grandchild) asserts the returned tree nests the
      grandchild under its parent, not the session root — covers R1, R4.
- [ ] A unit test asserts a session `.jsonl` with zero Agent tool_use
      events returns an empty tree with no exception — covers R3.
- [ ] A unit test asserts each tree node exposes `agentId`, `agentType`,
      `description`, `status`, `spawnDepth`, `started_ts` — covers R2.
- [ ] `scan_session_spawns()` is asserted (via test or `--json` diff) to
      not alter the output of any other `scan_*()` function — covers R5.
- [ ] Rendering the HTML dashboard for a repo with a spawning session shows
      a collapsible tree element for that session, and a repo with only
      non-spawning sessions renders unchanged from before this feature
      (visual/DOM diff or manual screenshot check) — covers R6, R7.
- [ ] End-to-end: run a real Claude Code session in a scratch repo that
      dispatches at least one Agent (Task) tool call, then run workboard
      against that repo and confirm the spawned agent appears as a node in
      the rendered tree with the correct status once it completes.

## Open questions

(none — all resolved above; ready for `/critique`)

## Parallelization

All four tasks form a single serial chain (01 → 02 → 03 → 04): each stage
consumes the data or wiring the previous stage produced (data layer →
scan_*() wiring → rendering → e2e/mirror), and all four edit overlapping
regions of the same file (`workboard.py`). No pair is both Touch-disjoint
and free of shared undecided design, so no task may run concurrently with
another per the decision-coupling test. Every task runs solo — no
`- Group:` lines apply.
