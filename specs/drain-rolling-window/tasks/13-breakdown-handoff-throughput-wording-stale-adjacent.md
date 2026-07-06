Status: draft
Discovered-from: specs/drain-rolling-window/tasks/09-fix-stale-group-mode-antigravity-handoff.md
Spec: ../SPEC.md
Blocking: no

# .claude/skills/breakdown/SKILL.md's Hand off section still describes throughput in pre-rolling-window terms

`.claude/skills/breakdown/SKILL.md`'s "Hand off" section (line ~122-123) tells the user to "ask [drain] for throughput to dispatch independent groups concurrently" — this doesn't use the retired literal phrase "group throughput mode" (so it wasn't in scope for task 09, which fixed the antigravity mirror's use of that exact phrase), but it still describes the pre-rolling-window mental model (asking for a one-shot concurrent dispatch of a group) rather than the rolling-window scheduler's actual behavior (a Parallel-window/Group: line opts a queue into a continuously-topped-up window, not a single all-members-concurrent launch). Worth rewording to match the current model, matching whatever wording task 09 used for the antigravity mirror's equivalent Hand off text.

## Acceptance

<!-- draft: needs runnable criteria before promotion -->
