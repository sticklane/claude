# Task 02: Verify the bare-vs-prefixed namespace hypothesis; document in agentprof

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers. ## Progress / ## Deferred questions are drain-written sections. -->

Status: done
Depends on: none
Priority: P2
Budget: 8 turns
Spec: ../SPEC.md (requirement R3)
Touch: agentprof/README.md, agentprof/SCHEMA.md

## Goal

The bare-vs-`agentic:`-prefixed agent-frame split is confirmed or refuted
against real transcripts, the answer is documented in agentprof's docs so
future profile readers interpret it correctly, and any stale shadow agent
copies discovered along the way are reported (deletion is task 03's call
if they're plugin-shadowing copies under `~/.claude/skills/` or similar).

## Touch

agentprof docs only. Do NOT edit `.claude/agents/*` (tasks 01/03 own that
side), and if a genuine agentprof code change looks warranted (e.g.
emitting a namespace label), file it as a suggestion under ## Deferred
questions for specs/agentprof-instrumentation — don't build it here.
agentprof has its own `scripts/check.sh`; docs-only changes don't need it,
but run it if anything under `agentprof/` beyond the two docs gets touched.

## Steps

1. From the pinned window (regenerate samples with
   `~/claude/agentprof/agentprof claude --since 2026-07-04T00:00:00Z -o /tmp/ns-samples.jsonl`),
   collect sessions producing bare frames (`agent:verifier`,
   `agent:scout`, `agent:implementation-worker`, `agent:critic`) and
   sessions producing the `agent:agentic:` forms.
2. Hypothesis check: do the bare-frame sessions run with cwd inside
   ~/claude (repo-local `.claude/agents/` definitions) while prefixed ones
   come from plugin dispatch elsewhere? Open 2–3 transcripts per side and
   confirm which agent definition file served each.
3. If any bare frame traces to a stale shadow copy of a plugin agent
   (e.g. under `~/.claude/agents/` or a repo that copied toolkit agents),
   name it in ## Progress with the path — flag for deletion review, don't
   delete another repo's files unilaterally from this task.
4. Write the explanation into agentprof's README (the stack-frames section
   that already explains `agent:`/`wf:` frames) and/or SCHEMA.md: bare
   name = repo-local `.claude/agents/` definition, `agentic:`-prefixed =
   plugin-served, same logical agent — plus one line on why both appear.
5. Adjust wording to whatever the evidence actually showed if the
   hypothesis is refuted.

## Acceptance

- [x] `grep -riqE 'agentic:' /Users/sjaconette/claude/agentprof/README.md /Users/sjaconette/claude/agentprof/SCHEMA.md` → exit 0
  - Evidence: exit 0; README.md L58/L63/L67 carry the new agent-frame paragraph (`agent:agentic:verifier`, `` `agentic:` prefix ``, `agentic:build`).
- [x] MANUAL: the hit explains the bare-vs-prefixed split with the confirmed mechanism (quote it as evidence)
  - Evidence: README.md paragraph states bare = "dispatched from a **repo-local `.claude/agents/` definition**", prefixed = "served by the installed **`agentic` plugin**", same logical agent; mechanism grounded in adapter code `internal/claude/claude.go:178` (`frame = "agent:" + meta.AgentType`, verbatim passthrough) vs skill-frame namespace-stripping at claude.go:465-477.
- [x] Evidence lines naming the transcripts checked (session IDs) and which agent-definition source each side traced to
  - BARE: session `eed20d5f-829c-4a98-94ea-1e780af8aede` (cwd `/Users/sjaconette/claude`) dispatched `subagent_type: implementation-worker`/`critic`/`scout` (bare) → repo-local `~/claude/.claude/agents/` (critic.md, implementation-worker.md, scout.md, verifier.md present). Also `61ec4803-...` (hub, Jul 3-4) with bare skill attribution `drain`/`idea`.
  - PREFIXED: session `5dcdc5c4-7776-4ac7-a064-8ed03a36fbd8` (cwd `/Users/sjaconette/fooszone`, no repo-local `.claude/agents/`) dispatched `subagent_type: agentic:critic`/`agentic:verifier` → installed `agentic` plugin. Also `b4bdc20a-...`/`9acb6dc5-...` (hub, Jul 6-7, prefixed).
  - Shadow-copy check (Step 3): `~/.claude/agents/` exists but is EMPTY; `~/hub/.claude/agents/` does not exist (hub's `.claude/skills/` holds only hub-specific meal-planning/priorities). No stale shadow copies of toolkit agents found; nothing to flag for deletion.

## Discovered

- Temporal attribution drift in hub transcripts (bare frames Jul 3-4, prefixed Jul 6+), consistent with hub moving to the installed plugin in early July — benign nuance covered by the doc's mechanism, no action
