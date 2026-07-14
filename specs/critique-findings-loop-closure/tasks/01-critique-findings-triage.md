# Task 01: Findings triage in /critique (R1)

Status: in-progress
Depends on: none
Priority: P1
Budget: 14 turns
Spec: ../SPEC.md (requirement R1; R2 is validated here too — see Acceptance)
Touch: .claude/skills/critique/SKILL.md

## Goal

`/critique` classifies every finding a NOT READY or READY WITH NITS verdict
returns into MECHANICAL (an edit with no judgment call: stale path/line
references, a non-deterministic or under-scoped acceptance command, a
missing runnable check, a format/header contract violation) or JUDGMENT
(ambiguity, scope, a missing design decision, a contested tradeoff).
MECHANICAL findings are applied directly to the target `SPEC.md` (or, when
`/critique` reviewed a plan document, that plan file — never a code diff)
unconditionally, committed, and the critic is re-run — bounded to the 2-4
cycle evaluator-optimizer cap in `.claude/rules/token-discipline.md`'s
"Dispatch authoring" (cite it, don't restate it). Findings still open after
the bound, and any JUDGMENT findings, are relayed/recorded exactly as
`/critique` does today — never silently dropped. The existing gate ("apply
fixes only if the user asks or the pipeline step requires READY") continues
to govern JUDGMENT findings; it does not apply to MECHANICAL ones.

## Touch

Only `.claude/skills/critique/SKILL.md`. Do not touch
`.claude/skills/drain/SKILL.md` or `.claude/skills/drain/reference.md` —
R2 (drain reusing this triage) requires no edit to either file; drain's
critique-intake step already invokes `/critique` via the Skill tool, so
this task's change reaches drain automatically. Do not touch
`antigravity/.agents/workflows/critique.md` or `.claude-plugin/plugin.json`
— the mirror update and version bump for this change are carried by the
spec's closing task (04), per this repo's "one closing task carries the
mirror + version bump" convention (CLAUDE.md's authoring conventions).
Do not add any hash-comparison or `critique-findings.md`-writing logic —
that is task 02's scope (R5/R6); this task only adds the
triage-classify-apply-recommit-recheck loop.

## Steps

1. Read `.claude/skills/critique/SKILL.md` in full (it is short — well
   under 100 lines).
2. Insert the MECHANICAL/JUDGMENT triage as a new step (or an expansion of
   existing step 4, "Apply fixes only if..."), stating:
   - The classification categories and examples, matching SPEC.md R1's
     wording.
   - MECHANICAL findings are applied unconditionally: edit the target file,
     commit (`fix: apply mechanical critique findings` or similar), re-run
     the critic agent.
   - The re-run loop is bounded to 2-4 cycles (cite
     `.claude/rules/token-discipline.md`'s "Dispatch authoring" rather than
     restating the cap's rationale).
   - Findings still open after the bound, and JUDGMENT findings from the
     first pass, are relayed/recorded via the existing step 2 relay
     behavior — never dropped silently.
   - Scope the file-target explicitly to `SPEC.md` or a plan file; a
     working-diff/code target is out of scope for auto-apply (state this
     plainly so a future reader doesn't extend MECHANICAL auto-apply to
     code).
3. Keep the existing `Breakdown-ready:` marker step (step 3) and the
   existing re-run-after-fixes step (step 5) intact; the new triage logic
   composes with them (an unconditional MECHANICAL apply is just a specific
   case of "apply fixes", now happening automatically rather than only on
   user-ask/pipeline-gate).
4. Update the `## Ultra path` section only if the panel-review path
   (3-5 critics) needs a note on how per-critic findings get merged before
   triage — likely not needed; leave it alone unless the single-critic
   triage logic doesn't obviously extend to a merged panel verdict.

## Acceptance

- [ ] `grep -c "MECHANICAL" .claude/skills/critique/SKILL.md` → ≥ 1 (today:
      0, confirmed absent)
- [ ] `grep -c "JUDGMENT" .claude/skills/critique/SKILL.md` → ≥ 1
- [ ] `bash evals/lint-ultra-gate.sh` → exits 0 (critique/SKILL.md carries
      a `## Ultra path` section; every "ultra" mention must stay within ±3
      lines of "active runtime profile" — don't let the new triage section
      land between an "ultra" mention and its marker)
- [ ] MANUAL: invoke `/critique` directly (attended, not via drain) against
      a real spec with a recorded NOT READY or READY WITH NITS verdict and
      at least one findable mechanical finding (e.g. a stale line-number
      reference or a non-deterministic grep in an existing
      `critique-findings.md` under `specs/`) — confirm the mechanical
      finding gets applied to that spec's `SPEC.md` automatically, a commit
      lands, and the critic is re-run without a human editing `SPEC.md` by
      hand.
