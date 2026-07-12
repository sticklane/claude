# Task 05: Diagnose and fix — dual baton trigger not preventing reprime pileup

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers. ## Progress / ## Deferred questions are drain-written sections. -->

Status: pending
Depends on: none
Priority: P1
Budget: 20 turns
Spec: ../SPEC.md (requirement R1, re-opened per EVIDENCE.md "Follow-up (2026-07-12)")
Touch: .claude/skills/drain/SKILL.md, .claude/skills/drain/reference.md, specs/drain-wake-cost/EVIDENCE.md

## Goal

Task 01 shipped a dual baton trigger (`max(2, 6−W)` verdicts, standing in
for "after ~4 verdicts OR when context is heavy") plus a degradation
override. A post-fix `agentprof` re-run (EVIDENCE.md, "Follow-up
(2026-07-12)") shows this has NOT reduced reprime pileup in real drain
sessions — three post-fix drain sessions (`55ae834e`, `80161f1c`,
`c2cec1dd`) still accumulated 3–11 reprimes each, and the share of ALL
sessions exceeding 3 reprimes rose from 26.4% to 29.4%. This task finds out
why the shipped trigger isn't firing early enough in practice, and ships a
concrete fix (or documents, with evidence, why none of the available levers
would help — see Out of scope for what that would look like).

## Touch

Only the two drain skill files plus this spec's EVIDENCE.md (to record
what you find). Do NOT touch drain-rolling-window's admission/merge
machinery (out of scope, same boundary task 01 respected) or
`.claude/rules/token-discipline.md` (owned by the separate
`specs/session-refresh-hook` spec, which covers the non-drain freehand
sessions — this task is drain-specific).

## Steps

1. Re-run `agentprof claude --since 2026-07-11T08:07:54Z -o
   /tmp/postfix.jsonl` (or reuse a fresh 7-day pull) and confirm the
   `55ae834e` / `80161f1c` / `c2cec1dd` reprime counts still reproduce —
   don't build on stale numbers.
2. Locate those three sessions' actual transcripts under `~/.claude`
   (agentprof's `--claude-dir`, default `~/.claude`; match by session ID
   prefix) and read the stretches immediately before each reprime event —
   was the baton-check step in `.claude/skills/drain/SKILL.md`'s "3a. Baton
   pass" ever reached between verdicts, or did the hub go many verdicts
   without evaluating it at all? Distinguish two hypotheses:
   a. **The check IS evaluated but the threshold is too loose** — e.g. W is
      computed low (narrow window) so `max(2, 6−W)` allows too many
      verdicts before baton, or the degradation override's trigger
      conditions (re-reading files, losing queue position, repeated
      failures) never matched even though context clearly ballooned.
   b. **The check is skipped** — the hub's turn-by-turn behavior doesn't
      actually re-evaluate the trigger after every verdict wake, so
      verdicts accumulate past the threshold before anything fires.
3. Based on which hypothesis the transcripts support, ship the smallest
   fix that closes the gap. Candidates (not exhaustive — pick based on what
   you actually observe): tighten the count formula for the window widths
   actually seen in practice; make the degradation-override conditions more
   sensitive (e.g. explicit turn-count-since-last-check bookkeeping in
   DRAIN-BATON.md, so the check is unmissable rather than judgment-based);
   or, if the transcripts show the model simply never re-checks the
   condition between wakes, restructure the instruction so the check is
   forced at a fixed point in the per-verdict loop rather than left to the
   model's discretion each time.
4. Append findings (which hypothesis, what you changed, why) to
   EVIDENCE.md under a new "Task 05 findings" subsection — this is the
   record future sessions read before touching the baton trigger again.
5. Do NOT claim the fix works from reasoning alone — the acceptance
   criteria below require a fresh measurement.

## Acceptance

- [ ] EVIDENCE.md has a "Task 05 findings" section stating which hypothesis
      (2a/2b/both) the transcript evidence supported, with session-id +
      quote/paraphrase citations
- [ ] `.claude/skills/drain/SKILL.md` and/or `reference.md` diff reflects
      the chosen fix, with the "3a. Baton pass" section still describing a
      single coherent rule (no contradictory trigger text left behind)
- [ ] `bash evals/lint-ultra-gate.sh` → exit 0 (drain is one of the four
      gated skills)
- [ ] MANUAL (deferred, needs another week of runs): a follow-up
      `agentprof claude --days 7` after this change ships shows drain-tagged
      sessions' share of ≥3-reprime sessions below the 29.4% measured in
      the 2026-07-12 follow-up — record the number when re-checked, don't
      leave the box unchecked indefinitely without a re-check date noted
