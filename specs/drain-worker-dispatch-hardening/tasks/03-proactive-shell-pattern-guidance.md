# Task 03: Proactive known-safe shell-pattern guidance

Status: pending
Depends on: 02
Priority: P2
Budget: 15 turns
Spec: ../SPEC.md (requirement R4)
Touch: .claude/skills/drain/reference.md, antigravity/.agents/workflows/drain.md

## Goal

The Worker prompt and the Headless fallback's inline prompt both carry
proactive guidance on which shell shapes get denied under restrictive
permission modes — stated once and cross-referenced between the two, not
duplicated — sitting alongside (never replacing) the existing reactive
retry-once-bare-command rule.

## Touch

Depends on task 02 landing first: both edit `reference.md`'s Headless
fallback region (02 changed the allowlist line inside the inline prompt
block at reference.md:892-918; this task adds guidance to the same
block plus the separate Worker prompt at reference.md:506-631) —
serialize to avoid overlapping edits in the 892-918 range. Do not touch
`.claude/skills/drain/SKILL.md` (task 05's scope) even though R4's
citation of the reactive retry rule lives near shell-safety content in
that neighborhood — confirm before editing that the retry rule itself
(reference.md:579, line-wrapped across two lines — the phrase "retry it
ONCE" is the safe single-line anchor, not the full sentence) is in
reference.md, not SKILL.md.

## Steps

1. Read the Worker prompt (`reference.md:506-631`) and the Headless
   fallback's inline prompt (`reference.md:892-918`) in full, confirming
   both restate the same reactive-retry contract (per the spec's Research
   grounding).
2. Write one canonical statement of known-safe shell-pattern guidance:
   avoid command substitution (`$(...)`), `for` loops, and multi-verb
   `&&`-chained commands in permission-gated Bash calls; use
   `! cmd | grep -q` rather than `cmd | ! grep`; handle `grep -c`'s
   exit-1-on-zero-matches explicitly (e.g. `grep -c … || true` when zero
   is an expected outcome). Place it once, and have the second location
   cross-reference it rather than repeat it in full. Use the literal
   phrase "known-safe shell patterns" (the spec's acceptance criterion
   greps for it).
3. Confirm this addition sits alongside, not in place of, the existing
   reactive "retry it ONCE" rule (reference.md:579) — do not remove or
   rewrite that rule.
4. Port the change into `antigravity/.agents/workflows/drain.md`'s
   corresponding Worker-prompt / Headless-fallback sections.
5. Commit, noting in the commit message that this restates guidance
   `codex/.agents/skills/drain/SKILL.md` already carries in its own
   Codex-adapted "Dispatch" section (per SPEC.md's Mirror obligations) —
   no codex edit is required by this task, just the note so the two don't
   silently drift.

## Acceptance

- [ ] `grep -c "known-safe shell patterns" .claude/skills/drain/reference.md` → at least 1
- [ ] `grep -c "retry it ONCE" .claude/skills/drain/reference.md` → at least 1 (the phrase wraps across two lines in the source, so anchor on this single-line-safe substring, not the full sentence — confirms the reactive rule survives)
- [ ] `grep -c "known-safe shell patterns" antigravity/.agents/workflows/drain.md` → at least 1
