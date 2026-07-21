Status: draft
Discovered-from: specs/ctx-dispatch-adoption/tasks/04-agentprof-ctx-telemetry.md
Spec: ../SPEC.md
Blocking: no

# agentprof's SkillInvocations reads the wrong JSON field, silently missing every real Skill call

`agentprof/internal/claude/skill_invocations.go`'s `skillInput` struct
(and its test fixtures) reads `input.command` for Skill tool_use blocks.
Real Claude Code Skill tool_use blocks carry the skill name under
`input.skill` instead (e.g. `{"skill":"agentic:ctx"}`, confirmed against
live `~/.claude` session transcripts) — task 04's worker made the exact
same mistake in its first draft for the new ctx-usage telemetry, caught
only by a critic pass. Because `skill_invocations.go`'s own test fixtures
fabricate `{"command":...}` inputs, its tests stay green while the
production path silently attributes zero Skill invocations. This is a
correctness bug in an already-shipped feature (`by_skill` attribution in
agentprof's Cost (7d) report), not new work — likely undercounting or
zeroing out skill-attribution numbers agentprof has been reporting.

## Acceptance

<!-- draft: needs runnable criteria before promotion -->
