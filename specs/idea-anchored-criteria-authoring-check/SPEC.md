Status: open
Priority: P2
Breakdown-ready: true

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
_before_ a change; the self-referential trap here is a phrase that will
only ever exist _because of_ the change meant to satisfy it, making
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
criterion before it is written into the SPEC.md file.

Placement: the new instruction is added as prose in step 3's body, AFTER
the closing ` ``` ` fence of the `specs/<kebab-slug>/SPEC.md` template block
(the fence closes at `.claude/skills/idea/SKILL.md:74`) — the same
placement step 4's own guidance already uses. It must never be added as a
line inside the fenced template itself: that template is copied verbatim
into every generated SPEC.md, so text placed inside it would become
literal boilerplate injected into every future spec rather than an
instruction `/idea` follows while drafting one. The template's
`## Acceptance criteria` bullet (`:66-70`) is only the pointer to WHICH
criteria the check applies to; the check's steps below are new prose
following the template, not template content:

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
target>` → 0 at authoring time; record 'phrase absent today, verified
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

R6. The closing task appends one new line to
`tests/mirror-procedure-manifest.txt` anchoring the "self-referential"
phrase for this pair — `.claude/skills/idea/SKILL.md|antigravity/.agents/skills/idea/SKILL.md|self-referential`
— so `tests/test_mirror_procedure_coverage.sh` actually exercises this
change instead of passing vacuously (it only checks phrases already
seeded in the manifest, and this pair currently has no line covering the
new step-3 content; see `.claude/rules/mirror-procedure-discipline.md`,
"the manifest grows every time a session finds and fixes a real
procedural gap").

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
- [ ] `grep -c "self-referential" antigravity/.agents/skills/idea/SKILL.md` →
      1 or more (phrase absent today, verified 2026-07-13 via the same
      command → 0).
- [ ] The closing task's own commit modifies `.claude-plugin/plugin.json`'s
      version line: `git show <closing-commit> -- .claude-plugin/plugin.json
| grep -q '^+.*"version"'` → match (per the version-bump-criteria
      pattern in `docs/memory/anchored-acceptance-criteria.md` — asserts the
      commit's own diff, not a pinned literal or a bare "differs from base").
- [ ] `grep -Fc '.claude/skills/idea/SKILL.md|antigravity/.agents/skills/idea/SKILL.md|self-referential' tests/mirror-procedure-manifest.txt` →
      1 or more (line absent today, verified 2026-07-13 via the same
      command → 0), satisfying R6.
- [ ] `bash tests/test_mirror_procedure_coverage.sh` passes — with R6's new
      manifest line in place, this is no longer a vacuous pass-either-way
      check: it fails if the antigravity mirror lacks the "self-referential"
      phrase the `.claude/` edit introduces.

## Open questions

None.

## Parallelization

No concurrent-safe groups. Task 02 depends on Task 01's exact landed
wording (mirror-procedure-discipline requires the antigravity mirror to
match the same steps/order/conditions Task 01 writes) and its own
manifest-line/version-bump work only makes sense once Task 01 has landed —
they fail the decision-coupling test (shared undecided content: Task 01's
prose is what Task 02 must read and mirror). Both tasks run solo, in
order.
