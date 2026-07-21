# Task 01: Compact HANDOFF.md header + informative multi-candidate disambiguation

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch, Rigor) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Priority values run P0 (highest) through P3; the header is optional — absent means P2. -->
<!-- Status vocabulary: pending → in-progress → done; also blocked (always with an Unblock: line), deferred, skipped, draft (stub awaiting promotion), and needs-verification (implementation complete, acceptance unverified — the verifier flips it to done; scanners treat it as open agent-bounded work, never a needs-attention flag). -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers, in every task file — and ## Progress / ## Deferred questions are drain-written sections (single writer, main checkout): workers report that content, never write it. -->

Status: done
Depends on: none
Priority: P1
Budget: 15 turns
Spec: ../SPEC.md (requirements R1, R2)
Touch: .claude/skills/handoff/SKILL.md, .claude/skills/resume-handoff/SKILL.md

## Goal

Every `HANDOFF.md` `/handoff` writes opens with a fixed header block
(`Task:`, `Status:`, `Next step:`, `Resume with:`, `Blocking on:`) ahead of
its existing, unchanged free-form prose. `/resume-handoff`'s step 1, when
multiple candidate `HANDOFF.md` files exist, reads each candidate's header
only (bounded read) and shows each candidate's `Task:`/`Status:` in the
`AskUserQuestion` option text instead of a bare path — the existing "ask
the user, never guess silently" behavior is unchanged; this only makes the
question answerable without opening any file.

## Touch

Exactly these two `SKILL.md` files. Do not touch
`hooks/handoff-resume/resume-check.sh` (its file-discovery logic is
unaffected — it only flags existence, never reads content) or any real
`HANDOFF.md` currently on disk.

## Steps

1. In `.claude/skills/handoff/SKILL.md`, add the mandatory header block as
   the first lines of the `HANDOFF.md` template/instructions it documents:
   `Task:` (a one-line name for the work — the field a resumer actually
   compares between candidates, since `Status:`/`Blocking on:` are often
   identical across two in-progress threads), `Status:`, `Next step:`,
   `Resume with:` (the skill/command to run), `Blocking on:`. State that
   these precede the existing free-form Task/Evidence/Gotchas prose
   sections, which are unchanged.
2. In `.claude/skills/resume-handoff/SKILL.md` step 1's "Multiple found"
   branch, change the behavior from "list the paths and ask the user
   which one via `AskUserQuestion`" to: read each candidate's compact
   header only (e.g. `head -n 10` per candidate — bounded, never the full
   file), then ask the user via `AskUserQuestion` with each option showing
   its `Task:` and `Status:` values alongside its path. Keep "never guess
   silently" explicit and unchanged — the skill still always asks; it
   never auto-selects. If two candidates' headers don't distinguish them
   (e.g. identical `Task:` values), ask anyway with whatever the headers
   show — no additional tiebreak logic.
3. Confirm the single-candidate path in `resume-handoff/SKILL.md` step 1
   is untouched.

## Acceptance

- [x] `grep -n "^Task:\|Resume with:\|Blocking on:" .claude/skills/handoff/SKILL.md`
      returns matches, including a required `Task:` field.
      → passed: matches on `Task:`/`Resume with:`/`Blocking on:` (a literal
      `Task:`-prefixed template line landed at column 0), see output above.
      Depth ceiling: prose-only template documentation, no runtime to
      exercise unattended — L0 is the ceiling; the behavioral complement
      is the MANUAL-PENDING criterion in the closing task's acceptance
      (an attended `/handoff` run producing a real header-shaped file).
- [x] `grep -n "compact header\|head -n" .claude/skills/resume-handoff/SKILL.md`
      returns a match specifically within the "Multiple found" branch (not
      elsewhere in the file).
      → passed: matches at lines 20-21, both inside the step 1 "Multiple
      found" branch, see output above.
      Depth ceiling: same as above.
- [x] `grep -n "AskUserQuestion" .claude/skills/resume-handoff/SKILL.md`
      still returns a match after the edit — confirms the change augments
      the existing question with header content rather than removing it
      (the never-guess-silently regression guard).
      → passed: still matches at line 23, see output above.
