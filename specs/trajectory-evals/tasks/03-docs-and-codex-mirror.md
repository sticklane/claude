# Task 03: document EVAL_TRANSCRIPT (.claude leg + codex mirror)

Status: in-progress
Depends on: 01
Priority: P1
Budget: 10 turns
Spec: ../SPEC.md (requirements R4, part of R5)
Touch: .claude/skills/evals/SKILL.md, .claude/skills/evals/reference.md, codex/.agents/skills/evals/SKILL.md

## Goal

`.claude/skills/evals/SKILL.md` and `reference.md` document
`EVAL_TRANSCRIPT`, keep artifact assertions primary, and drop the stale
"v1 grades artifacts only" framing. The codex mirror
(`codex/.agents/skills/evals/SKILL.md`) gets the same treatment in this
same task, per CLAUDE.md's mirroring convention that a task touching one
of the four codex real-content SKILL.md files must carry the codex
counterpart in its own Touch — not a separate task, since both edit the
same "v1 grades artifacts only" doctrine line and splitting them risks
one landing without the other.

## Touch

Do not touch `antigravity/.agents/workflows/evals.md` or
`.claude-plugin/plugin.json` — those belong to task 04 (the closing
task, which also handles the antigravity carve-out decision).

## Steps

1. Read `.claude/skills/evals/SKILL.md` and `reference.md` in full,
   locate the "v1 grades artifacts only" line (currently around
   `SKILL.md:11`) and the ~10-line failure-message budget rule (keep
   this rule verbatim — R4 requires trajectory failures respect the same
   budget).
2. Add documentation of `EVAL_TRANSCRIPT`: what it is, that it's opt-in
   per scenario (no existing `assert.sh` needs editing), and one worked
   trajectory-assertion example (illustrative — does not need to match
   task 02's exact scenario verbatim, just demonstrate the pattern, e.g.
   `grep -q '"subagent_type":"scout"' "$EVAL_TRANSCRIPT"`).
3. Remove the "v1 grades artifacts only" sentence — replace it with
   language naming both v1 (artifact grading, still primary) and v2
   (opt-in trajectory assertions via `EVAL_TRANSCRIPT`).
4. In `codex/.agents/skills/evals/SKILL.md`, find line 19's "v1 grades
   artifacts only" phrasing (the direct contradiction) and update it the
   same way. Leave line 41's "never a transcript" phrasing untouched —
   it's about the grader's ~10-line failure-message return budget to the
   orchestrator, not about whether `assert.sh` can read a transcript,
   and is not contradictory (same treatment as the identical line in
   `.claude/skills/evals/SKILL.md` and
   `antigravity/.agents/workflows/evals.md`, neither touched by this
   task either).

## Acceptance

- [ ] `grep -q "EVAL_TRANSCRIPT" .claude/skills/evals/SKILL.md`
- [ ] `grep -q "EVAL_TRANSCRIPT" .claude/skills/evals/reference.md`
- [ ] `! grep -q "v1 grades artifacts only" .claude/skills/evals/SKILL.md`
- [ ] `grep -q "EVAL_TRANSCRIPT" codex/.agents/skills/evals/SKILL.md`
- [ ] `! grep -q "v1 grades artifacts only" codex/.agents/skills/evals/SKILL.md`
- [ ] `grep -q "never a transcript" codex/.agents/skills/evals/SKILL.md`
      (line 41's budget rule is confirmed still present, unchanged)
