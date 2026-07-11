# Task 01: Trace the fable-verifier leak and land the matching outcome

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers. ## Progress / ## Deferred questions are drain-written sections. -->

Status: done
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

- [x] Mechanism named with transcript evidence from the pinned window (session IDs + the plugin version or override found — quote in evidence lines)
  - Evidence: sessions 5dcdc5c4/b5cd2c76/7e277508/ee0f4482 transcripts reference `cache/agentic-toolkit/agentic/0.6.2`; that snapshot pins `model: inherit` → resolved to the session's fable-5 model (5dcdc5c4: 527 fable main-line msgs); 5 verifier dispatches carried no explicit model override. Verifier re-derived the grep independently. See evidence/01-verifier-leak-trace.md.
- [x] Exactly one R1 outcome landed; for (a): `test -f /Users/sjaconette/claude/docs/memory/verifier-tier-leak.md` → exit 0 and it names the version boundary and the immutable-cache mechanism
  - Evidence: outcome (a) — `docs/memory/verifier-tier-leak.md` created; names the boundary (`inherit` ≤0.7.0 → `sonnet` ≥0.8.3; repo pin at commit 01062e9/0.7.15) and the immutable-cache mechanism. Verifier PASS (literal `test -f` targets the main-checkout path which materializes on merge; substance confirmed in-tree). See evidence/01-verifier-leak-trace.md.
- [x] Evidence line confirming no files under `~/.claude/plugins/cache/` were modified (`find ~/.claude/plugins/cache/agentic-toolkit -newer /Users/sjaconette/claude/specs/agent-tier-leaks/SPEC.md -type f | wc -l` → 0)
  - Evidence: literal find → 1, sole hit `0.8.13/.in_use/25950` is a live-`claude` PID lock marker (harness runtime churn, not content); `find … -not -path '*/.in_use/*'` → 0. No plugin content modified. Verifier confirmed via `ps -p 25950`. See evidence/01-verifier-leak-trace.md.
