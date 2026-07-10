# Task 01: Defer stub-intake promotions past the authoring run; strip Original report at conversion

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Priority values run P0 (highest) through P3; the header is optional — absent means P2. -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers, in every task file — and ## Progress / ## Deferred questions are drain-written sections (single writer, main checkout): workers report that content, never write it. -->

Status: pending
Depends on: none
Priority: P0
Budget: 30 turns
Spec: ../SPEC.md (requirements R1, R3, R5)
Touch: .claude/skills/drain/SKILL.md, .claude/skills/drain/reference.md, antigravity/.agents/workflows/drain.md, .claude-plugin/plugin.json

## Goal

Stub-intake PASS/DECISION-SHAPED no longer flips `Status: draft` →
`pending` in the authoring run. It writes `Promotion-ready: true` +
`Promoted-by-run: <run-token>` instead, leaving `Status: draft` (so the
stub is excluded from dispatch and the terminal test by drain's existing
draft-handling machinery). Only a later drain invocation whose OWN
`Run-token:` differs from the stub's `Promoted-by-run:` value converts it
to `Status: pending` — after the remote-divergence check and after that
invocation's owner-lease claim succeeds — and strips `## Original report`
from the file in that SAME commit. Stub intake excludes any
`Promotion-ready: true` stub from its own re-scan in every subsequent
baton generation of the authoring run. The exit checklist distinguishes
`Promotion-ready: true` drafts (already gated, will auto-flip) from
ordinary drafts (awaiting human authorship), and its "Promoted this run"
section prints the exact `Demoted:` line to reverse each promotion. The
antigravity mirror carries the equivalent contract; `plugin.json`'s
version is bumped.

## Touch

Do not touch `.claude/skills/drain/screen-stub.sh` (task 02's scope) or
the exit checklist's "Defaults taken" section / `## Answers` vs
`## Decisions` scanning (task 03's scope) — this task's exit-checklist
edits are limited to sections covering draft/promotion status (section 5,
"Draft stubs awaiting promotion") and stub-intake activity (section 6,
"Promoted this run"). Do not touch `docs/human-gates.md` reason 4's
wording or expand the screen's threat-model scope — the spec's R6
explicitly defers those to a maintainer decision; this task must not
silently resolve them.

## Steps

1. Read `.claude/skills/drain/reference.md`'s current "Stub intake
   (assess → gate → act)" section and its Act step in full, and
   `.claude/skills/drain/SKILL.md`'s "Stub intake" section and step-4 exit
   checklist (sections 2, 5, 6) in full — line numbers in the spec are
   approximate, work from current content.
2. Rewrite the Act step's PASS/DECISION-SHAPED outcome: write
   `Promotion-ready: true` + `Promoted-by-run: <run-token>` instead of
   flipping `Status: pending`. Document that these headers persist across
   every step-1 re-entry and baton generation (committed file, same
   durability as `Stub-intake-failed:`).
3. Add the stub-intake in-scope exclusion: a `Status: draft` stub already
   carrying `Promotion-ready: true` is excluded from stub intake's own
   scan from the moment of promotion onward.
4. Document the owner-lease re-claim invariant explicitly: a re-claim of
   an already-held lease writes the session's EXISTING `Run-token:` back,
   never mints a new one; only a launch with no baton to adopt mints one.
5. Add the step-1 conversion procedure: convert `Promotion-ready: true` →
   `Status: pending` ONLY when the current invocation's own `Run-token:`
   differs from the stub's `Promoted-by-run:` value — explicitly NOT
   gated on `DRAIN-BATON.md` presence/absence — after the remote-
   divergence check and after the owner-lease claim succeeds, skipping
   re-run of assess/gate. In the SAME commit as this conversion, strip
   `## Original report` from the file (state explicitly that the audit
   trail survives via the earlier stub-intake Act-step commit's git
   history, not via an unchanged current-state block).
6. Update SKILL.md's exit-checklist section 5 to exclude
   `Promotion-ready: true` drafts (list only ordinary un-gated drafts);
   add them to section 6 as a labeled addendum reading "already authored
   and gated — will auto-promote the next time a drain run with a
   different Run-token touches this spec." Do NOT add a new top-level
   checklist section — SKILL.md documents this as a fixed
   "seven-section checklist"; adding an eighth section would shift every
   later section's number, which task 03's own "section 2" reference
   (and this task's own "section 5"/"section 6" references) assume stay
   stable.
7. Update reference.md's two terminal readings ("drained, listing the
   drafts for human promotion" and "drained pending promotion") so a
   queue holding ONLY `Promotion-ready: true` drafts reports as genuinely
   drained, not blocked on a human.
8. Update section 6's "Promoted this run" format to print the exact
   `Demoted:` line a human would paste to reverse each promotion.
9. Port the equivalent contract into
   `antigravity/.agents/workflows/drain.md` in that mirror's own
   paraphrased voice (per docs/memory/workboard-mirror-verbatim.md).
10. Bump `.claude-plugin/plugin.json`'s version.
11. Verify: read back every edited section and confirm the two fixtures
    below are satisfiable by the documented procedure (prose-consistency
    check, not a required live run).

## Acceptance

- [ ] reference.md's Act step documents `Promotion-ready: true` +
      `Promoted-by-run: <run-token>` (not a `Status: pending` flip) as
      stub intake's PASS/DECISION-SHAPED outcome, persisting across every
      step-1 re-entry and baton generation of the authoring run.
- [ ] reference.md's stub-intake in-scope definition documents excluding
      any `Status: draft` stub already carrying `Promotion-ready: true`.
- [ ] reference.md explicitly states the owner-lease re-claim invariant:
      a re-claim writes the session's EXISTING `Run-token:` back, never a
      freshly-minted one.
- [ ] reference.md's step 1 procedure documents converting
      `Promotion-ready: true` → `Status: pending` ONLY when the current
      invocation's own `Run-token:` differs from the stub's
      `Promoted-by-run:` value — explicitly NOT gated on `DRAIN-BATON.md`
      presence/absence — after the remote-divergence check and after the
      owner-lease claim succeeds.
- [ ] reference.md documents the SAME commit performing this conversion
      also stripping `## Original report`, with the audit-trail-via-
      earlier-commit rationale stated explicitly.
- [ ] SKILL.md's exit-checklist section 5 excludes `Promotion-ready: true`
      drafts; they appear only in section 6, labeled distinctly from
      "awaiting your promotion."
- [ ] reference.md's two terminal readings are updated so a queue holding
      ONLY `Promotion-ready: true` drafts reports as genuinely drained.
- [ ] Section 6's "Promoted this run" format includes the literal
      `Demoted:` line text to reverse each promotion.
- [ ] A fixture (inspectable on the documented procedure): stub PASS in
      generation 1, baton pass to generation 2 within the same run → the
      stub is still `Status: draft` with `Promotion-ready: true` at
      generation 2's step 1, not `pending`.
- [ ] A fixture (inspectable on the documented procedure): stub PASS at
      the exhaustion trigger, then — WITHIN THE SAME GENERATION, no baton
      pass — the batch interview answers a deferred task and returns to
      step 1 → the stub is STILL `Status: draft` at that re-entry, because
      the re-entry's `Run-token:` matches the stub's `Promoted-by-run:`.
- [ ] `git diff $(git merge-base main HEAD)..HEAD -- antigravity/` shows `antigravity/.agents/workflows/drain.md`
      changed, carrying the equivalent contract in paraphrased voice (a
      content-coverage check: fetch, Promotion-ready, Promoted-by-run,
      Run-token-mismatch conversion, Original-report strip).
- [ ] `git diff $(git merge-base main HEAD)..HEAD -- .claude-plugin/plugin.json | grep '"version"'`
      shows the version increased.
- [ ] `git diff $(git merge-base main HEAD)..HEAD -- docs/human-gates.md` → empty (R6 not silently
      resolved).
- [ ] `git diff $(git merge-base main HEAD)..HEAD -- .claude/skills/drain/screen-stub.sh` → empty
      (task 02's scope, not touched here).
