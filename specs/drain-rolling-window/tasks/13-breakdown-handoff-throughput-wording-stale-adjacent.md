Status: pending
Discovered-from: specs/drain-rolling-window/tasks/09-fix-stale-group-mode-antigravity-handoff.md
Spec: ../SPEC.md
Blocking: no

# .claude/skills/breakdown/SKILL.md's Hand off section still describes throughput in pre-rolling-window terms

`.claude/skills/breakdown/SKILL.md`'s "Hand off" section (line ~122-123) tells the user to "ask [drain] for throughput to dispatch independent groups concurrently" — this doesn't use the retired literal phrase "group throughput mode" (so it wasn't in scope for task 09, which fixed the antigravity mirror's use of that exact phrase), but it still describes the pre-rolling-window mental model (asking for a one-shot concurrent dispatch of a group) rather than the rolling-window scheduler's actual behavior (a Parallel-window/Group: line opts a queue into a continuously-topped-up window, not a single all-members-concurrent launch). Worth rewording to match the current model, matching whatever wording task 09 used for the antigravity mirror's equivalent Hand off text.

Decision (2026-07-06): task 09 is done and its wording is available — `antigravity/.agents/skills/breakdown/SKILL.md` line ~123 now says "its rolling window hands you concurrent ... launches". Reword `.claude/skills/breakdown/SKILL.md`'s Hand off text (~lines 122-123, "ask it for throughput to dispatch independent groups concurrently") to describe the rolling-window model (a `Parallel-window:`/`Group:` line opts a queue into a continuously-topped-up window), matching task 09's wording.

## Acceptance

- [ ] `! grep -q 'dispatch independent groups concurrently' .claude/skills/breakdown/SKILL.md` → exits 0 (stale pre-rolling-window phrase gone; currently present)
- [ ] `grep -qi 'rolling window' .claude/skills/breakdown/SKILL.md` → exits 0 (Hand off names the rolling window; currently only the hyphenated spec slug appears)
