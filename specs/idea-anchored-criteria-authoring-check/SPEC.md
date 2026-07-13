Status: open
Priority: P2

# idea: apply the anchored-acceptance-criteria check at drafting time, not just breakdown time

## Problem

`docs/memory/anchored-acceptance-criteria.md` documents a doctrine for
grep/count-based acceptance criteria: anchor on a phrase confirmed absent
from the current file, never pin an unsatisfiable numeric bound, and never
let a criterion pass vacuously. That doctrine is written for and applied at
BREAKDOWN time (`/breakdown` turning a SPEC.md's criteria into task files).
It is not applied earlier, at `.claude/skills/idea/SKILL.md`'s step 3
("Write the spec"), where acceptance criteria actually originate.

This gap let a self-referential criterion through: a task's grep criterion
checked for a placeholder string that the same task's own change would
introduce as an incidental artifact, independent of whether the task's
substantive requirement was actually implemented — so the criterion could
never fail, regardless of correctness. This is the same failure class the
memory file already names ("vacuous grep" — a criterion that green-checks a
worker that did the wrong thing), but from the opposite temporal direction:
the memory file's guidance checks a phrase against the file's state
*before* a change; the self-referential trap here is a phrase that will
only ever exist *because of* the change meant to satisfy it, making
absence-today insufficient by itself as a check. `/idea` drafted the
criterion with neither check applied, so it reached breakdown (and then a
worker) already broken, causing a spurious DEFER when the worker correctly
judged the criterion unsatisfiable-as-stated.

## Solution

Extend `.claude/skills/idea/SKILL.md` step 3 ("Write the spec") so that,
immediately after drafting each grep/count-based acceptance criterion (the
bullet list under the `## Acceptance criteria` template, `.claude/skills/idea/SKILL.md:66-70`),
`/idea` applies the anchored-acceptance-criteria check from
`docs/memory/anchored-acceptance-criteria.md` (cited, not restated) to that
criterion before it is written into the SPEC.md file:

1. For a criterion asserting a phrase or count is present/passing, run
   `grep -ci '<phrase>' <target file>` (or the equivalent count check)
   against the file's CURRENT on-disk state and confirm the expected
   result actually differs from today's — i.e. the phrase is presently
   absent (or the count presently fails the bound), never pin a bound the
   file already violates or satisfies.
2. Additionally reject (and rewrite) a criterion whose target phrase is
   itself content that this same spec's own planned Requirements would
   introduce as an incidental byproduct rather than as evidence of the
   requirement's actual behavior — the self-referential trap: if a worker
   could satisfy the grep by writing the literal search string alone,
   without implementing the requirement's substance, the criterion is
   rejected and must be rewritten to assert something that depends on the
   requirement actually being implemented (e.g. an observable behavior, a
   runnable test, or a phrase tied to functional content rather than a
   bare marker string).
3. Record the check's outcome inline next to the criterion in the SPEC.md
   draft (e.g. "phrase absent today, verified <date>"), matching the
   memory file's existing recording convention, so `/breakdown` and a
   later worker don't have to re-derive it.

This applies the same doctrine `/breakdown` already uses, one step earlier
in the pipeline, so a broken criterion is caught before it is ever written
to disk rather than surviving to cause a mid-drain deferral.

Because this edits `.claude/skills/idea/SKILL.md` and `idea` is not one of
the four explicit-invocation skills (`build`/`drain`/`autopilot`/`evals`),
the antigravity mirror at `antigravity/.agents/skills/idea/SKILL.md`
(its equivalent step 3, `antigravity/.agents/skills/idea/SKILL.md:41-68`)
needs the matching update, and `.claude-plugin/plugin.json`'s `version`
needs a bump — no codex mirror exists for `idea`, so no codex change is
needed.

## Research grounding

> "**Vacuous grep** (three separate specs): `grep -qi 'frontier' SKILL.md`
> and `grep -qi 'worktree root' reference.md` both already matched
> pre-existing, unrelated text — the criterion green-checks a worker that
> writes nothing. Fix pattern: anchor on a NEW distinctive literal phrase
> the requirement mandates verbatim ... and run `grep -ci '<phrase>' <every
> target>` → 0 at authoring time; record 'phrase absent today, verified
> <date>' in the criterion so the verifier knows it can't pass vacuously."
> — `docs/memory/anchored-acceptance-criteria.md:10-17`

## Requirements

R1. `.claude/skills/idea/SKILL.md` step 3 ("Write the spec") must instruct
    that, for every grep/count-based acceptance criterion drafted in that
    step, the anchored-acceptance-criteria check (citing
    `docs/memory/anchored-acceptance-criteria.md`, not restating its
    content) is applied to the criterion before it is written into the
    SPEC.md — not deferred to `/breakdown`.

R2. The step-3 instruction must require confirming, against the CURRENT
    on-disk file (not a hypothetical post-change state), that the
    criterion's target phrase/count is presently absent/unsatisfied, per
    the memory file's existing "run `grep -ci` at authoring time" pattern.

R3. The step-3 instruction must additionally require rejecting a criterion
    whose target phrase is itself an incidental artifact this same spec's
    own Requirements would introduce (the self-referential trap) — i.e. a
    criterion a worker could satisfy by writing only the literal search
    string, without implementing the requirement's actual behavior — and
    rewriting it to assert something dependent on genuine implementation.

R4. The antigravity mirror (`antigravity/.agents/skills/idea/SKILL.md`,
    its own step 3 "Write the spec") receives the same procedural addition
    (same steps, same order, same stated conditions per
    `.claude/rules/mirror-procedure-discipline.md` — cited, not restated).

R5. `.claude-plugin/plugin.json`'s `version` is bumped from its value at
    the time this spec's closing task is authored.

## Out of scope

- Building tooling/automation to run the grep check programmatically inside
  `/idea` (e.g. a hook or script) — this spec only adds the instruction to
  the skill body; execution stays a model-driven step, matching how
  `/breakdown` already applies the same doctrine today.
- Changing `/breakdown`'s own existing application of this doctrine.
- Retroactively fixing any already-drafted spec's acceptance criteria.
- The `codex/` port — `idea` has no codex mirror (only
  `drain`/`build`/`autopilot`/`evals` do), so no codex change applies.

## Acceptance criteria

- [ ] `grep -c "anchored-acceptance-criteria" .claude/skills/idea/SKILL.md` →
      1 or more (phrase absent today, verified 2026-07-13 via
      `grep -c "anchored-acceptance-criteria" .claude/skills/idea/SKILL.md`
      → 0).
- [ ] `grep -c "anchored-acceptance-criteria" antigravity/.agents/skills/idea/SKILL.md` →
      1 or more (phrase absent today, verified 2026-07-13 via
      `grep -c "anchored-acceptance-criteria" antigravity/.agents/skills/idea/SKILL.md`
      → 0).
- [ ] `grep -c "self-referential" .claude/skills/idea/SKILL.md` → 1 or more
      (phrase absent today, verified 2026-07-13 via the same command → 0).
- [ ] The closing task's own commit modifies `.claude-plugin/plugin.json`'s
      version line: `git show <closing-commit> -- .claude-plugin/plugin.json
      | grep -q '^+.*"version"'` → match (per the version-bump-criteria
      pattern in `docs/memory/anchored-acceptance-criteria.md` — asserts the
      commit's own diff, not a pinned literal or a bare "differs from base").
- [ ] `bash tests/test_mirror_procedure_coverage.sh` (if present) passes,
      or MANUAL: confirm by inspection that the antigravity step-3 edit
      states the same three sub-checks (current-state grep, self-referential
      rejection, inline outcome recording) in the same order as the
      `.claude/` edit.

## Open questions

None.
