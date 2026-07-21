# Task 03: Retrofit the repo's current HUMAN.md entry to the new grammar

Status: done
Depends on: 01
Priority: P2
Budget: 10 turns
Spec: ../SPEC.md (requirement R5)
Touch: HUMAN.md

## Goal

If `HUMAN.md`'s `## Agent-filed blockers` section still contains an entry
whose source path is `specs/trajectory-evals/critique-findings.md`, that
entry is rewritten to follow the new `Blocks:` grammar from task 01. If no
such entry exists (already resolved and removed), this task is a no-op.

## Touch

Only `HUMAN.md`. Do not touch `.claude/rules/human-blockers.md` (already
landed by task 01 — read it, don't edit it), `.claude/skills/drain/reference.md`
(task 02), or `antigravity/.agents/workflows/drain.md` (task 04).

## Steps

1. Read `.claude/rules/human-blockers.md`'s current grammar (landed by
   task 01, which this task depends on) to confirm the exact `Blocks:`
   clause format.
2. Check `HUMAN.md`'s `## Agent-filed blockers` section for an entry whose
   `<source path>` is `specs/trajectory-evals/critique-findings.md`.
   - If present: rewrite that line to the new grammar, adding a `Blocks:`
     clause. This entry's type is `decide` (a NOT-READY critique-intake
     finding), so per task 02's fixed-phrase pinning its impact is
     `Blocks: breakdown of this spec into dispatchable tasks`. Keep the
     rest of the line's content (date, source path, type, action text)
     intact — only add the `Blocks:` clause; do not otherwise reword the
     entry unless it also needs the plain-language tightening from R2 (if
     you do reword the action text, keep it materially the same meaning,
     just more readable).
   - If absent (already resolved and removed by another session): do
     nothing to `HUMAN.md`; this task's acceptance check accounts for
     this case.

## Acceptance

- [x] If an entry with source path `specs/trajectory-evals/critique-findings.md`
      exists in `HUMAN.md`: `grep 'trajectory-evals/critique-findings.md' HUMAN.md | grep -c 'Blocks:'`
      → 1. If no such entry exists, this check is skipped, not failed —
      record which case applied (present-and-retrofitted, or
      already-resolved-and-absent) in your final evidence. (Entry present
      today at HUMAN.md:5 with no `Blocks:` clause — piped count 0,
      verified 2026-07-19 — so the check cannot pass vacuously.) Depth
      ceiling: L0 on a one-line prose entry — behavioral complement is a
      manual-pending human read: the HUMAN.md owner confirms the
      retrofitted line names both the ask and its impact and is
      actionable without opening the source file.
      Evidence: present-and-retrofitted — grep piped count → 1 (verifier
      PASS 2026-07-20); appended `— Blocks: breakdown of this spec into
    dispatchable tasks` to HUMAN.md:5. Behavioral complement (L0
      manual-pending human read) left for the HUMAN.md owner.
