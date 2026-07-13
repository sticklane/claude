# Task 01: Add the anchored-acceptance-criteria check to /idea's step 3

Status: pending
Depends on: none
Priority: P1
Budget: 8 turns
Spec: ../SPEC.md (requirements R1, R2, R3)
Touch: .claude/skills/idea/SKILL.md

## Goal

`.claude/skills/idea/SKILL.md` step 3 ("Write the spec") instructs `/idea`
to apply the anchored-acceptance-criteria check — from
`docs/memory/anchored-acceptance-criteria.md`, cited not restated — to
every grep/count-based acceptance criterion it drafts, before that
criterion is written into the SPEC.md file. The check has three parts: (1)
confirm the criterion's target phrase/count is presently absent/unsatisfied
against the file's CURRENT on-disk state, (2) additionally reject and
rewrite a criterion whose target phrase is itself an incidental byproduct
of this same spec's own Requirements (the self-referential trap — a
criterion a worker could satisfy by writing only the literal search
string, without implementing the requirement's actual behavior), (3)
record the check's outcome inline next to the criterion (e.g. "phrase
absent today, verified <date>").

## Touch

Only `.claude/skills/idea/SKILL.md`. Do not touch
`antigravity/.agents/skills/idea/SKILL.md`, `.claude-plugin/plugin.json`,
or `tests/mirror-procedure-manifest.txt` — those are Task 02's closing
work, done after this task's exact wording exists to mirror.

## Steps

1. Read `.claude/skills/idea/SKILL.md` step 3 in full (roughly lines
   45–75), including the fenced ` ```markdown ` SPEC.md template that
   spans it.
2. Confirm today's absence of both anchor phrases (matches the spec's
   "verified 2026-07-13" claims — re-verify with today's date since this
   may run later):
   - `grep -c "anchored-acceptance-criteria" .claude/skills/idea/SKILL.md`
   - `grep -c "self-referential" .claude/skills/idea/SKILL.md`
     Both must print `0` before you edit. If either is already non-zero,
     stop and report — the spec's premise no longer holds.
3. Add new prose to step 3, placed AFTER the closing ` ``` ` fence of the
   SPEC.md template block (never inside the fence — that template is
   copied verbatim into every future generated spec, so an instruction
   placed inside it would become boilerplate text injected into every
   spec rather than an instruction `/idea` follows while drafting one).
   The new prose must, at minimum:
   - Cite `docs/memory/anchored-acceptance-criteria.md` by path (do not
     restate its content) as the doctrine being applied.
   - State that this check applies to every grep/count-based acceptance
     criterion, applied immediately after drafting it and before it is
     written into the SPEC.md — not deferred to `/breakdown`.
   - Instruct running `grep -ci '<phrase>'` (or the equivalent count
     check) against the target file's CURRENT on-disk state, confirming
     the criterion's expected result actually differs from today's.
   - Instruct rejecting and rewriting a criterion whose target phrase is
     itself an incidental byproduct of the same spec's own Requirements
     (the self-referential trap), naming the failure mode explicitly with
     the literal word "self-referential" somewhere in the new prose, and
     requiring the rewrite depend on genuine implementation (an observable
     behavior, a runnable test, or a phrase tied to functional content).
   - Instruct recording the check's outcome inline next to the criterion
     in the SPEC.md draft, matching the memory file's "phrase absent
     today, verified <date>" convention.
4. Keep the new prose as numbered steps or a short checklist consistent
   with this skill's existing style (see step 4's own numbered-list style
   just below it for the pattern).

## Acceptance

- [ ] `grep -c "anchored-acceptance-criteria" .claude/skills/idea/SKILL.md` → 1 or more.
- [ ] `grep -c "self-referential" .claude/skills/idea/SKILL.md` → 1 or more.
- [ ] The new prose sits after the closing fence of the SPEC.md template
      block, not inside it: `awk '/^```markdown$/{f=1} f&&/^```$/{print NR; exit}' .claude/skills/idea/SKILL.md`
      prints a line number, and both anchor-phrase line numbers from the
      two checks above are greater than it (confirm with
      `grep -n "anchored-acceptance-criteria\|self-referential" .claude/skills/idea/SKILL.md`).
- [ ] `bash evals/lint-ultra-gate.sh` → exit 0 (idea/SKILL.md is one of the
      four ultra-path skills this gate checks; the edit must not disturb
      its "ultra" mentions' ±3-line marker pairing).
- [ ] Re-read the edited step 3 once and confirm by inspection it states
      all three sub-checks from the Goal above, in that order (current-
      state grep → self-referential rejection → inline outcome
      recording) — this is the exact content Task 02 must mirror
      verbatim in procedure.
