Status: done
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

Run from the `agentprof/` directory unless noted.

- [x] `skillInput` reads the real field: `grep -c 'json:"skill"' internal/claude/skill_invocations.go` returns 1, and `grep -c 'json:"command"' internal/claude/skill_invocations.go` returns 0 (no Skill-input field still reads `command`).
- [x] No test fixture fabricates a `Skill` tool_use with the wrong input field: `grep -rn '"name":"Skill","input":{"command"' *.go internal/` returns nothing (Bash tool_use blocks, which legitimately use `input.command`, are untouched).
- [x] The core parse test uses the real field and passes: `go test ./internal/claude/ -run TestSkillInvocationsPairsResultsCommandTagsAndUserTurns` is `ok`, and that test's fixture now sends `{"skill":...}` (it fails against the pre-fix `command`-reading code — confirmed red-first).
- [x] The whole suite and canonical check are green: `bash scripts/check.sh` exits 0 (format-check, vet, `go test ./...` all pass), so the skillcheck e2e table again attributes invocations to named skills instead of an empty name.
