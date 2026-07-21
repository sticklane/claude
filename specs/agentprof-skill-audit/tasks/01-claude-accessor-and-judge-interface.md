# Task 01: internal/claude SkillInvocations accessor + judge interface

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch, Rigor) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Priority values run P0 (highest) through P3; the header is optional — absent means P2. -->
<!-- Status vocabulary: pending → in-progress → done; also blocked (always with an Unblock: line), deferred, skipped, draft (stub awaiting promotion), and needs-verification (implementation complete, acceptance unverified — the verifier flips it to done; scanners treat it as open agent-bounded work, never a needs-attention flag). -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers, in every task file — and ## Progress / ## Deferred questions are drain-written sections (single writer, main checkout): workers report that content, never write it. -->

Status: pending
Depends on: none
Priority: P0
Budget: 24 turns
Spec: ../SPEC.md (requirements R2, R9, R12)
Touch: agentprof/internal/claude/skill_invocations.go, agentprof/internal/claude/skill_invocations_test.go, agentprof/internal/judge/judge.go, agentprof/internal/judge/cli.go, agentprof/internal/judge/cli_test.go, agentprof/internal/judge/fake.go

## Goal

Two foundational, independently-testable pieces every other task in this
spec builds on exist and are unit-tested: (1) a new exported
`SkillInvocations` accessor on `agentprof/internal/claude` that surfaces
what `internal/claude`'s unexported internals already parse but don't
expose — raw `Skill` `tool_use` blocks paired with their `tool_result`,
each invocation's preceding `<command-name>` tag (if any), and whether an
intervening user turn preceded it; (2) a `judge` package (new,
`agentprof/internal/judge/`) providing a `Judge` interface mirroring
`agentprof/internal/naming/cli.go`'s `Namer`/`CLINamer` shape, a real
CLI-backed implementation (`claude -p <prompt> --model <tier>
--output-format json`, `CLAUDE_CONFIG_DIR` set to a scratch dir per
invocation), and a `Fake` implementation for tests that records every
prompt/tier it was called with.

## Touch

Only the files listed in the header. Do not touch `agentprof/main.go` or
`agentprof/cmd_skillcheck*.go` (task 04's scope) or write any
`skillcheck`-specific classification logic here — this task is purely the
two shared building blocks.

## Steps

1. Read `agentprof/internal/claude/claude.go` (the existing unexported
   `transcriptLine`/`turnRec`/`commandSkillFrame` types and the exported
   `Collect`/`CollectWithOptions` walk) to find where per-line `cwd`,
   `<command-name>` tags, and tool_use/tool_result pairing already happen
   in the shared JSONL walk — build `SkillInvocations` on top of that
   existing walk rather than re-parsing.
2. Write a failing test in `skill_invocations_test.go` first: a small
   fixture transcript with a model-auto-triggered `Skill` invocation, one
   preceded by a `<command-name>` tag, and one occurring inside an
   assistant turn with no new preceding user message (a self-chain shape).
   Assert `SkillInvocations` returns all three with the right
   name/args/result/command-tag/preceding-user-turn fields.
3. Implement `SkillInvocations` to pass.
4. Read `agentprof/internal/naming/cli.go` and `cli_test.go` for the
   subprocess-invocation and command-construction-test patterns to mirror.
5. Write a failing test in `judge/cli_test.go` first, mirroring
   `naming/cli_test.go`'s approach: assert the built `*exec.Cmd` (never
   executed) carries `--model <tier>`, `--output-format json`, and
   `CLAUDE_CONFIG_DIR=<scratch>` in its `Env` — proving the self-pollution
   guard R12 requires without a real subprocess call.
6. Implement the `Judge` interface, `CLINamer`-equivalent CLI
   implementation, and `Fake` to pass. `Fake` must record every
   prompt+tier it receives and let a test assert on that recorded call
   list.

## Acceptance

- [ ] `cd agentprof && go build ./...` succeeds.
- [ ] `cd agentprof && go test ./internal/claude/... -run TestSkillInvocations`
      passes (red-first: confirm it fails before the implementation step).
- [ ] `cd agentprof && go test ./internal/judge/...` passes, including the
      command-construction test asserting `CLAUDE_CONFIG_DIR` is set on the
      built command without executing it (red-first).
