Status: deferred
Discovered-from: specs/agentprof-skill-audit/tasks/04-cli-wiring-and-report.md
Spec: ../SPEC.md
Blocking: no

# SkillInvocation lacks a source-line and per-invocation user-turn text

`internal/claude.SkillInvocation` (task 01) exposes no source-line, so
skillcheck's findings can only cite `transcript_ref` at file granularity
(`<path>`, not `<path>:<line>`) — see task 04's Decisions. It also exposes
no per-invocation user-turn text, so trigger-judge grounding falls back to
the session's joined user turns instead of precise per-invocation text.
Adding both would let skillcheck emit true `path:line` citations and
tighter trigger grounding.

## Acceptance

<!-- draft: needs runnable criteria before promotion -->

## Deferred questions

A dispatched worker confirmed this stub is not dispatchable as written:
its `## Acceptance` section is a draft placeholder with zero runnable
criteria, and it carries no `Touch:` header. The proposed change (adding
a source-line field and a per-invocation user-turn-text field to
`internal/claude.SkillInvocation`) touches consumers owned by already-
`done` tasks 01 and 04 (the exported struct and the JSON report contract,
R10) — threading a new field through without agreed, scoped acceptance
risks reopening settled work.

**Question:** should this task be promoted with (1) runnable acceptance
criteria — e.g. a test asserting a new source-line field (path + line of
the `Skill` tool_use) and a user-turn-text field populate from a synthetic
fixture, plus a `cmd_skillcheck` test asserting `transcript_ref` renders
`<path>:<line>` per SPEC R10's report-shape example — and (2) a `Touch:`
header (minimally `agentprof/internal/claude/skill_invocations.go`,
`agentprof/internal/claude/skill_invocations_test.go`, and the
`cmd_skillcheck*.go` consumer(s))? No other pending task depends on this
one (`Blocking: no`).
