# Task 03: docs — absence-fallacy scope caution reflects tool-emitted guard

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch, Rigor) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Priority values run P0 (highest) through P3; the header is optional — absent means P2. -->
<!-- Status vocabulary: pending → in-progress → done; also blocked (always with an Unblock: line), deferred, skipped, draft (stub awaiting promotion), and needs-verification (implementation complete, acceptance unverified — the verifier flips it to done; scanners treat it as open agent-bounded work, never a needs-attention flag). -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers, in every task file — and ## Progress / ## Deferred questions are drain-written sections (single writer, main checkout): workers report that content, never write it. -->

Status: blocked
Unblock: run: grep -q "ABSENCE FALLACY" .claude/skills/ctx/SKILL.md && echo "R7 landed — safe to flip to pending" || echo "specs/ctx-skill-token-doctrine R7 has not landed yet"
Depends on: 01, 02
Priority: P2
Budget: 10 turns
Spec: ../SPEC.md (requirements R5)
Touch: .claude/skills/ctx/SKILL.md, antigravity/.agents/skills/ctx/SKILL.md

## Goal

The skill scope cautions' absence-fallacy entry (authored by
specs/ctx-skill-token-doctrine R7) is updated to say the tool now emits
the guard itself (task 01's boundary note + suggested command), and the
VERIFY ABSENCE ladder guidance points at the emitted command instead of
instructing the agent to construct its own grep from scratch.

## Touch

This is SLOT 6 of the SKILL.md editor registry in
specs/ctx-skill-token-doctrine's Landing order (../../ctx-skill-token-doctrine/SPEC.md)
— edit `.claude/skills/ctx/SKILL.md` and its antigravity mirror in the
SAME commit, per that spec's landing-order constraint. Do not touch any
other section of either SKILL.md beyond the absence-fallacy caution and
the VERIFY ABSENCE ladder guidance.

## Steps

1. Confirm `Status: blocked`'s `Unblock:` check passes (R7 has landed —
   `.claude/skills/ctx/SKILL.md` already contains an "ABSENCE FALLACY"
   caution written by that spec's own task). Do not proceed if it hasn't;
   report DEFERRED/BLOCKED per the standard contract instead of guessing
   at content that doesn't exist yet.
2. Update the absence-fallacy caution text to state that `ctx refs`/`sig`
   no-match now emits the boundary note + suggested bounded grep command
   itself (task 01), rather than instructing the agent to independently
   remember the caveat and construct its own check.
3. Update the VERIFY ABSENCE ladder guidance (wherever it lives in the
   SKILL.md) to point at the emitted command as the concrete next step,
   rather than generic "grep to verify" prose.
4. Apply the identical content update to
   `antigravity/.agents/skills/ctx/SKILL.md` in the same commit (paraphrased
   port is fine — mirror-procedure-discipline governs content parity, not
   verbatim text; see `.claude/rules/mirror-procedure-discipline.md`).

## Acceptance

- [ ] `grep -A5 "ABSENCE FALLACY" .claude/skills/ctx/SKILL.md` shows updated
      text describing the tool-emitted guard (not the pre-task-01 "you
      must remember to grep" phrasing).
- [ ] `grep -A5 "ABSENCE FALLACY" antigravity/.agents/skills/ctx/SKILL.md`
      shows the equivalent updated content.
- [ ] `git diff --stat` for this task's commit touches only the two
      SKILL.md files listed in Touch.
