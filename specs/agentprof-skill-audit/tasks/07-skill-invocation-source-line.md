Status: pending
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
