# Task 03: Tool-call ceilings for critic and verifier, INCOMPLETE verdict, both repos

Status: pending
Depends on: none
Budget: 20 turns
Spec: ../SPEC.md (requirements R5, R8-part; R9 note)

## Goal

`.claude/agents/critic.md` and `.claude/agents/verifier.md` each gain a
numeric tool-call ceiling line containing the phrase "tool-call
ceiling": ~25 for critic with scout-style best-effort reporting when it
hits; ~20 for verifier, EXEMPTING per-criterion acceptance commands from
the count (it must exercise every criterion). On hitting its ceiling the
verifier's verdict is INCOMPLETE — never PASS — listing the unexercised
criteria; its output-contract line becomes "Verdict line: `PASS` /
`FAIL` / `INCOMPLETE`" in BOTH `.claude/agents/verifier.md` and
`antigravity/.agents/skills/verifier/SKILL.md`. Ceiling mirrors also go
to `antigravity/.agents/skills/critic/SKILL.md`. Deliberately do NOT
edit caller files (autopilot, build, drain): their routing already
treats anything non-PASS as not-passed, so INCOMPLETE is non-PASS by
construction. Do NOT bump plugin.json — the combined bump (R9) is owned
by global task 99 in specs/review-fixes.

## Touch

- `.claude/agents/critic.md`
- `.claude/agents/verifier.md`
- `antigravity/.agents/skills/critic/SKILL.md`
- `antigravity/.agents/skills/verifier/SKILL.md`

## Steps

1. Add the tool-call ceiling line (~25, best-effort reporting on hit) to
   `.claude/agents/critic.md`.
2. Add the tool-call ceiling line (~20, acceptance-command exemption,
   INCOMPLETE-on-ceiling with unexercised criteria listed) to
   `.claude/agents/verifier.md`, and update its output-contract line to
   "Verdict line: `PASS` / `FAIL` / `INCOMPLETE`".
3. Mirror both changes into
   `antigravity/.agents/skills/critic/SKILL.md` and
   `antigravity/.agents/skills/verifier/SKILL.md` (including the
   three-verdict contract line in the verifier mirror).
4. Confirm no caller edits: `git diff --name-only` shows only the four
   files above.

## Acceptance

- [ ] `grep -q "tool-call ceiling" .claude/agents/critic.md && grep -q "tool-call ceiling" .claude/agents/verifier.md && grep -q "INCOMPLETE" .claude/agents/verifier.md && grep -q "INCOMPLETE" antigravity/.agents/skills/verifier/SKILL.md` (R5)
- [ ] `grep -q "tool-call ceiling" antigravity/.agents/skills/critic/SKILL.md && grep -q "tool-call ceiling" antigravity/.agents/skills/verifier/SKILL.md` (R8-part)
