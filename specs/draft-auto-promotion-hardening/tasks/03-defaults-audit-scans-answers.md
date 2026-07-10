# Task 03: Exit checklist's "Defaults taken" section also scans stub-intake `## Answers` defaults

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Priority values run P0 (highest) through P3; the header is optional — absent means P2. -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers, in every task file — and ## Progress / ## Deferred questions are drain-written sections (single writer, main checkout): workers report that content, never write it. -->

Status: done
Depends on: none
Priority: P2
Budget: 8 turns
Spec: ../SPEC.md (requirement R4)
Touch: .claude/skills/drain/SKILL.md

## Goal

The exit checklist's "Defaults taken" section (step 4, section 2) also
surfaces DECISION-SHAPED stub-intake promotions that recorded a reversible
default under `## Answers` — today it only scans `## Decisions`, so a
drain-authored default for a decision-shaped stub is invisible to the one
audit section built specifically to surface unilateral defaults.

## Touch

Do not touch section 5 ("Draft stubs awaiting promotion") or section 6
("Promoted this run") — task 01's scope, which also edits nearby exit-
checklist sections; this task is limited to section 2 ("Defaults taken")
only. Do not touch `.claude/skills/drain/reference.md`'s Act step (task
01's scope — where `## Answers` defaults are written) or
`.claude/skills/drain/screen-stub.sh` (task 02's scope).

## Steps

1. Read `.claude/skills/drain/SKILL.md`'s step-4 exit checklist in full,
   particularly section 2 ("Defaults taken") and its current documented
   scan source (`## Decisions`).
2. Update section 2's documented scan to ALSO include stub-intake
   `## Answers` defaults recorded by a DECISION-SHAPED promotion — a
   drain-authored reversible default for a decision-shaped stub must
   surface here, distinctly noting it came from stub intake (not an
   ordinary `## Decisions` entry) if the two are otherwise
   indistinguishable in format.
3. Verify: read back the edited section and confirm both sources
   (`## Decisions` and stub-intake `## Answers` defaults) are explicitly
   named as scan inputs.

## Acceptance

- [x] SKILL.md's exit-checklist section 2 ("Defaults taken") documents
      scanning stub-intake `## Answers` defaults in addition to
      `## Decisions` entries.
      Evidence: verifier PASS (evidence/03-defaults-audit-scans-answers.md);
      section 2 now reads "from `## Decisions` plus each DECISION-SHAPED
      stub's `## Answers` default (from stub intake)".
- [x] A fixture (inspectable on the documented procedure): a
      DECISION-SHAPED stub promoted with a reversible default recorded
      under `## Answers` → the documented section-2 procedure surfaces it
      in the exit checklist, distinctly attributed to stub intake.
      Evidence: verifier PASS; "(from stub intake)" tag scopes to the
      decision-shaped stub default (cross-ref SKILL.md line ~382), not
      every `## Answers` entry.
- [x] `git diff $(git merge-base main HEAD)..HEAD -- .claude/skills/drain/SKILL.md` shows only
      section 2's scan-source text changed — sections 5 and 6 (task 01's
      scope) are untouched by this diff.
      Evidence: verifier PASS; single hunk at lines 456-457, sections 5/6
      unchanged; file still 501 lines.

## Discovered

- The antigravity mirror (`antigravity/.agents/workflows/drain.md` section 2) still carried the old "Defaults taken" text after this task, and the spec's own acceptance criteria require the mirror to carry R1-R5, not just R1/R3. Task 03's Touch didn't include it (a gap in the breakdown). Closed directly by drain (not a new task): ported the same "(from stub intake)" wording into the mirror's section 2, and bumped plugin.json (0.8.31 → 0.8.32) in the same commit.
