# Task 04: agentprof per-session ctx adoption telemetry

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch, Rigor) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Priority values run P0 (highest) through P3; the header is optional — absent means P2. -->
<!-- Status vocabulary: pending → in-progress → done; also blocked (always with an Unblock: line), deferred, skipped, draft (stub awaiting promotion), and needs-verification (implementation complete, acceptance unverified — the verifier flips it to done; scanners treat it as open agent-bounded work, never a needs-attention flag). -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers, in every task file — and ## Progress / ## Deferred questions are drain-written sections (single writer, main checkout): workers report that content, never write it. -->

Status: done
Depends on: none
Priority: P2
Budget: 14 turns
Spec: ../SPEC.md (requirement R5)
Touch: agentprof/

## Goal

agentprof reports a per-session ctx-usage metric for sessions whose cwd
resolves to an indexed repo (a repo with `.context/` at its root): the
count of Bash tool calls whose command invokes
`ctx <tree|sig|refs|deps|at|map|notes|show>` plus Skill-tool invocations
of `agentic:ctx`. Sessions in non-indexed repos contribute zero even if
their transcripts contain ctx-shaped commands. The metric surfaces
alongside the existing skill attribution. Baseline for comparison
(2026-07-21 review): 0 outside the fooszone survey + rollout sessions.

## Touch

Follow agentprof's existing cmd/test layout (`agentprof/cmd_claude.go`
et al. — TDD per quality-discipline; note `~/claude` has no
scripts/check.sh gate and mirror test basenames collide in one pytest
run, but agentprof is Go: `go test ./...` inside `agentprof/` is the
gate). Do not touch skill files or plugin.json.

## Steps

1. Write the failing Go test first: fixture transcript (JSONL) with (a)
   an indexed-repo session containing 2 Bash `ctx refs`/`ctx tree`
   calls + 1 `agentic:ctx` Skill invocation → metric = 3; (b) a session
   whose cwd is NOT an indexed repo containing the same shapes →
   metric = 0; (c) a Bash command where `ctx` appears only as a
   substring (e.g. a Go `getExecutionCtx` grep) → not counted.
2. Implement: detect indexed-repo cwd (`.context/` existence at the
   session's cwd root, resolved at analysis time), match Bash commands
   with a word-boundary `ctx <verb>` pattern, count `agentic:ctx` Skill
   frames via the existing skill-attribution path.
3. Surface the metric in the report output next to skill attribution.

## Acceptance

- [x] `cd agentprof && go test ./...` → exit 0, including new tests covering the three fixture cases above (indexed counts, non-indexed excluded, substring not counted) — all 16 pkgs ok; new `internal/claude/ctx_usage_test.go` (`TestCollectCountsCtxUsageForIndexedRepoSession` = 3, `TestCollectExcludesCtxUsageForNonIndexedRepoSession` = 0, substring `getExecutionCtx` excluded) + `costsummary` `TestBuildSessionsSectionSurfacesCtxUsage` (evidence: specs/ctx-dispatch-adoption/evidence/04-agentprof-ctx-telemetry.md)
- [x] `cd agentprof && go vet ./...` → exit 0 (no output; verifier-confirmed, evidence file)
- [x] Report output over the fixture shows the ctx metric field — `costsummary.SessionStat.CtxUsage` (json `ctx_usage`) asserted via typed struct access (`s.Sessions["s1"].CtxUsage == 3`), not output strings; kept out of by_*/totals rollups (evidence file). Verifier mutation-test confirmed the substring-exclusion case is load-bearing, not vacuous.

## Decisions

- 2026-07-21: Counted ctx usage over main-loop calls only (subagent
  samples excluded), matching the existing per-session p50/p90 scope.
  Reversible: attach `ctx_usage` in `collect`'s subagent loop and drop
  the agent-frame filter in `sessionStats`.
- 2026-07-21: Surfaced as `SessionStat.CtxUsage`, excluded from
  by_*/totals (per-session-only, alongside skill attribution).
  Reversible: remove the `ctxUsageMetric` skip in `Build` to also roll it
  into by_project/by_skill/totals.
- 2026-07-21: Skill match strips the plugin namespace so both
  `agentic:ctx` and bare `ctx` count (mirrors `normalizeSkillFrame`).
  Reversible: match `agentic:ctx` exactly.

## Discovered

- The pre-existing `agentprof/internal/claude/skill_invocations.go`
  `skillInput` struct (and its test fixtures) reads `input.command` for
  Skill invocations, but real Claude Code Skill tool_use blocks carry the
  name under `input.skill` — the same wrong field this task's own first
  draft used before a critic pass caught it (verified against live
  `~/.claude` transcripts). The existing `SkillInvocations`
  skill-attribution path therefore silently misses every real Skill call
  in production, masked green by fabricated `{"command":...}` fixtures.
  See task 10.
