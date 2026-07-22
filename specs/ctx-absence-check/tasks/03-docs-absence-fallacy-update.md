# Task 03: docs — absence-fallacy scope caution reflects tool-emitted guard

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch, Rigor) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Priority values run P0 (highest) through P3; the header is optional — absent means P2. -->
<!-- Status vocabulary: pending → in-progress → done; also blocked (always with an Unblock: line), deferred, skipped, draft (stub awaiting promotion), and needs-verification (implementation complete, acceptance unverified — the verifier flips it to done; scanners treat it as open agent-bounded work, never a needs-attention flag). -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers, in every task file — and ## Progress / ## Deferred questions are drain-written sections (single writer, main checkout): workers report that content, never write it. -->

Status: blocked
Unblock: run: grep -q "ABSENCE FALLACY" .claude/skills/ctx/SKILL.md && grep -q "Reading ladder" .claude/skills/ctx/SKILL.md && echo "R7 and R2 both landed — safe to flip to pending" || echo "specs/ctx-skill-token-doctrine R2 (Reading ladder) and/or R7 (ABSENCE FALLACY) has not landed yet"
Depends on: 01, 02
Priority: P3
Budget: 10 turns
Spec: ../SPEC.md (requirements R5)
Touch: .claude/skills/ctx/SKILL.md, antigravity/.agents/skills/ctx/SKILL.md

## Goal

The skill scope cautions' absence-fallacy entry (authored by
specs/ctx-skill-token-doctrine R7) is updated to say the tool now emits
the guard itself (task 01's boundary note + suggested command), and the
Reading ladder's (specs/ctx-skill-token-doctrine R2) "symbol not indexed"
escalation trigger — the concrete rung this spec's own VERIFY ABSENCE CUJ
maps to — points at the emitted command instead of generic "grep to
verify" prose.

## Touch

This is SLOT 6 of the SKILL.md editor registry in
specs/ctx-skill-token-doctrine's Landing order (../../ctx-skill-token-doctrine/SPEC.md)
— edit `.claude/skills/ctx/SKILL.md` and its antigravity mirror in the
SAME commit, per that spec's landing-order constraint. Do not touch any
other section of either SKILL.md beyond the absence-fallacy caution and
the Reading ladder's "symbol not indexed" trigger text. Caution: this slot
sits behind slots 4 (ctx-minified-skip R5) and 5 (ctx-dead-code-zones R4)
in that same registry — if either hasn't landed yet when you start, treat
that as a fresh reason to stop DEFERRED (registry-order collision risk),
not just proceed because this task's own Unblock check passed.

## Steps

1. Confirm `Status: blocked`'s `Unblock:` check passes (both R2's "Reading
   ladder" section and R7's "ABSENCE FALLACY" caution already exist in
   `.claude/skills/ctx/SKILL.md`). Do not proceed if either is missing;
   report DEFERRED/BLOCKED per the standard contract instead of guessing
   at content that doesn't exist yet.
2. Update the absence-fallacy caution text to state that `ctx refs`/`sig`
   no-match now emits the boundary note + suggested bounded grep command
   itself (task 01), rather than instructing the agent to independently
   remember the caveat and construct its own check. Include the literal
   phrase "now emits the guard itself" (or exact equivalent) so the change
   is mechanically verifiable.
3. In the Reading ladder section, update the "symbol not indexed"
   escalation trigger's guidance to point at the emitted suggested command
   as the concrete next step, rather than generic "grep to verify" prose.
   Include the literal phrase "suggested bounded grep" (or exact
   equivalent) so the change is mechanically verifiable.
4. Apply the identical content update to
   `antigravity/.agents/skills/ctx/SKILL.md` in the same commit (paraphrased
   port is fine — mirror-procedure-discipline governs content parity, not
   verbatim text; see `.claude/rules/mirror-procedure-discipline.md`).

## Acceptance

- [ ] `grep -c "now emits the guard itself" .claude/skills/ctx/SKILL.md`
      → 0 today (verified 2026-07-21), 1+ after the fix — confirms the
      absence-fallacy caution edit actually landed (anchored on new text,
      not just that the ABSENCE FALLACY section exists at all).
- [ ] `grep -c "suggested bounded grep" .claude/skills/ctx/SKILL.md`
      → 0 today (verified 2026-07-21), 1+ after the fix, AND that literal
      appears within 10 lines of "not indexed" (confirms it landed on the
      Reading ladder's escalation trigger, not somewhere unrelated) —
      confirms the ladder edit actually happened (this is the criterion
      the original breakdown was missing).
- [ ] Read `antigravity/.agents/skills/ctx/SKILL.md`'s ABSENCE FALLACY
      caution and "not indexed" trigger text: each states, in its own
      words, that the tool now emits the guard/suggested command itself
      (content parity, not verbatim — `.claude/rules/mirror-procedure-discipline.md`).
      If the exact phrases from the `.claude` edits happen to fit
      naturally, reusing them is fine; paraphrase is not required.
- [ ] `git diff --stat` for this task's commit touches only the two
      SKILL.md files listed in Touch.
