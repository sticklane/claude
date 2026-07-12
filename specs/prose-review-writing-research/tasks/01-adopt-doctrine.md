# Task 01: Adopt NN/g and Google style-guide doctrine into prose-review's reference.md

Status: done
Depends on: none
Priority: P2
Budget: 15 turns
Spec: ../SPEC.md (requirements R1–R7)
Touch: .claude/skills/prose-review/reference.md

## Goal

`.claude/skills/prose-review/reference.md` carries six new, verified-source
additions (guidelines-not-rules framing, reader-test inverted-pyramid/
subheading scoring, an antipattern-rubric citation, a named vague-link-text
bad example with accessibility framing, an acronym/jargon checklist item,
and a `## Why this matters` DORA note) exactly as specified in
`../SPEC.md`'s Solution and Requirements sections. `SKILL.md` is untouched.
All additions stay advisory — no rubric item becomes blocking.

## Touch

Only `.claude/skills/prose-review/reference.md` changes. Do not edit
`.claude/skills/prose-review/SKILL.md` (R7 requires it stay byte-for-byte
unchanged) or any file under `specs/prose-review/` (a separate, already-
existing spec — out of scope per `../SPEC.md`'s Out of scope section).

## Steps

1. Read `../SPEC.md` in full, then `.claude/skills/prose-review/reference.md`
   in full — the six insertion points are named precisely in the spec's
   Solution section by heading/line anchor; re-locate by heading text if
   line numbers have drifted since the spec was written.
2. Make the six edits, in this order (top of file to bottom, so later edits
   don't shift earlier line anchors mid-edit):
   a. Insert the new `## Why this matters` section (R6) immediately after
      the existing intro paragraph, before `## The nine-item rubric`.
   b. Add the Morkes & Nielsen citation to the antipattern rubric items
      covering hyperbole/verbosity/self-celebratory language (R3), and
      make conciseness an explicitly rewarded property, not just an
      anti-flagged one. Do not cite the refuted 47%-scannability figure.
   c. Insert the guidelines-not-rules paragraph (R1) at the top of the
      `## Google-style essentials Vale can't check` section, using the
      exact verbatim priority sentence the spec specifies.
   d. Extend the "descriptive link text" bullet with the "Learn More"
      named example and accessibility rationale (R4).
   e. Add the new sixth bullet introducing the acronym/jargon convention
      with NN/g's every-occurrence tension noted as a caveat (R5).
   f. Extend the reader-test procedure with inverted-pyramid and
      subheading-quality scoring, alongside its existing comprehension
      probes (R2).
3. Confirm `SKILL.md` has no diff: `git diff --stat .claude/skills/prose-review/SKILL.md`
   should print nothing.
4. Create a scratch file named `README.md` in a throwaway directory (not
   committed to the repo) containing a "Learn More" link, a promotional/
   hyperbolic sentence, and a paragraph structure that buries its
   conclusion below unrelated background — then run `/prose-review`
   (read-only report mode) against it and confirm all three are flagged.
5. Run the acceptance greps below yourself before marking this task done.

## Acceptance

- [x] `grep -c "developers.google.com/tech-writing" .claude/skills/prose-review/reference.md` → ≥1 — verifier confirmed 1
- [x] `grep -c "project-specific conventions first" .claude/skills/prose-review/reference.md` → ≥1 — verifier confirmed 1, verbatim sentence present
- [x] `grep -c "how-users-read-on-the-web" .claude/skills/prose-review/reference.md` → ≥1 — verifier confirmed 1, plus inverted-pyramid/subheading scoring present
- [x] `grep -c "concise-scannable-and-objective" .claude/skills/prose-review/reference.md` → ≥1 — verifier confirmed 1
- [x] `grep -c "47%" .claude/skills/prose-review/reference.md` → 0 — verifier confirmed 0
- [x] `grep -c "Learn More" .claude/skills/prose-review/reference.md` → ≥1 — verifier confirmed 1, accessibility rationale present
- [x] `grep -ci "acronym\|jargon" .claude/skills/prose-review/reference.md` → ≥1 — verifier confirmed 1, every-occurrence-vs-first-use tension stated
- [x] `grep -c "dora.dev" .claude/skills/prose-review/reference.md` → ≥1 — verifier confirmed 1
- [x] `grep -c "Why this matters" .claude/skills/prose-review/reference.md` → ≥1 — verifier confirmed 1, DORA sentence uses "associated with (not proven to cause)"
- [x] `git diff --stat .claude/skills/prose-review/SKILL.md` → no output — verifier confirmed empty, byte-for-byte unchanged
- [x] End-to-end: `/prose-review` run against a scratch `README.md` (vague
      link, promotional sentence, buried conclusion) flags all three under
      the updated rubric; report format is otherwise unchanged. — run live
      in the parent /build session: "Learn More" flagged via the descriptive
      link-text bullet, the hyperbolic sentence flagged via rubric items
      5/9, and the buried conclusion flagged via the reader test's new
      inverted-pyramid probe; table + reader-test-answers-above-table format
      unchanged.
