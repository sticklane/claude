# Task 01: Trace the fable-verifier leak and land the matching outcome

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers. ## Progress / ## Deferred questions are drain-written sections. -->

Status: in-progress
Depends on: none
Priority: P1
Budget: 12 turns
Spec: ../SPEC.md (requirement R1)
Touch: .claude/agents/verifier.md, docs/memory/verifier-tier-leak.md

## Goal

The $74 fable-model verifier spend is traced to its mechanism with
transcript evidence from the pinned 2026-07-04→11 window, and exactly one
R1 outcome is landed: (a) confirmation it's the pre-0.8.3 `model: inherit`
plugin snapshots → document the version boundary + immutable-cache
mechanism; (b) an overriding dispatch path corrected; or (c) a deliberate
escalation written into the verifier agent doc as policy. Expected
outcome is (a) per the spec's Problem section — but confirm, don't assume.

## Touch

The verifier agent doc and a new memory note only. NEVER edit files under
`~/.claude/plugins/cache/` (immutable versioned snapshots). Do NOT touch
`.claude/rules/` (owned by specs/drain-wake-cost/tasks/02 — the single
token-discipline.md writer across all three agentprof specs) or
`agentprof/` (task 02). If outcome (a)
holds and verifier.md itself needs no edit, the memory note alone is the
documentation home — do not edit verifier.md just to have touched it (an
agent-def edit triggers the task-03 mirror/bump obligation).

## Steps

1. Read ../SPEC.md R1 and ../../drain-wake-cost/EVIDENCE.md. Identify the
   fable-verifier sessions: run
   `~/claude/agentprof/agentprof claude --since 2026-07-04T00:00:00Z -o /tmp/leak-samples.jsonl`
   (or use the pinned profile with
   `go tool pprof -tagfocus` — the samples route is simpler) and filter
   for stacks containing `agent:agentic:verifier` + `claude-fable-5`;
   collect the `session` labels.
2. Open those sessions' transcripts under `~/.claude/projects/` and
   determine which plugin version served the verifier (the agent's system
   prompt / meta records the plugin path incl. version) and whether any
   dispatch passed an explicit model override.
3. Land the matching outcome. For (a): write
   `docs/memory/verifier-tier-leak.md` — the version boundary
   (`model: inherit` through 0.7.x, `model: sonnet` from 0.8.3), the
   immutable-cache mechanism (stale plugin versions keep serving old
   pins until the install updates), and the check command; add a pointer
   line to `docs/memory.md`'s index if one exists. For (b)/(c): the
   dispatch-site fix or the escalation policy in verifier.md, and note in
   ## Progress that task 03's mirror/bump now applies.
4. Report which outcome landed and the evidence trail in ## Progress.

## Acceptance

- [ ] Mechanism named with transcript evidence from the pinned window (session IDs + the plugin version or override found — quote in evidence lines)
- [ ] Exactly one R1 outcome landed; for (a): `test -f /Users/sjaconette/claude/docs/memory/verifier-tier-leak.md` → exit 0 and it names the version boundary and the immutable-cache mechanism
- [ ] Evidence line confirming no files under `~/.claude/plugins/cache/` were modified (`find ~/.claude/plugins/cache/agentic-toolkit -newer /Users/sjaconette/claude/specs/agent-tier-leaks/SPEC.md -type f | wc -l` → 0)
