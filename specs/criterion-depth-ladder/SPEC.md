# Criterion depth ladder: anti-gaming gates for acceptance criteria

Status: open

## Problem

A 2026-07-19 survey of ~90 acceptance criteria across 13 specs found ~40%
are literal-phrase greps a worker could satisfy by typing the searched
phrase without implementing the requirement's behavior; the largest single
spec (`specs/mirror-procedure-discipline`, 21 tasks) gates almost entirely
on a grep-manifest, and live examples of the self-referential trap exist
(`specs/critique-findings-loop-closure/tasks/01` greps for the words
"MECHANICAL"/"JUDGMENT"; `specs/rigor-tier/tasks/01` greps for the literal
`Rigor:`). The anchoring doctrine
(`docs/memory/anchored-acceptance-criteria.md`) eliminates criteria that
pass with NO work, but not criteria that pass with TRIVIAL work: an
anchored new phrase still only proves the phrase was typed. The two agents
positioned to catch this fire wrong: the critic has no acceptance-criteria
attack instruction at all (`.claude/agents/critic.md` blocks READY only on
unmapped/missing criteria; `.claude/skills/critique/SKILL.md` triages only
"non-deterministic or under-scoped" commands as MECHANICAL), and the
verifier's strong anti-gaming rules (`.claude/agents/verifier.md`:
exercise every criterion, overfitting = FAIL) fire after implementation,
when a shallow criterion has already shaped the work.

## Solution

Name the depth of a criterion and gate on it at the three points that
already exist — authoring (/idea, /breakdown), adversarial review
(critic), and verification (verifier) — rather than adding a new stage.
The ladder and the new failure pattern live in
`docs/memory/anchored-acceptance-criteria.md` (the doctrine home the
skills already cite); skills cite it, never restate it. For prose-only
artifacts (most of this toolkit), text-presence is often the honest
ceiling — the mechanism legalizes that with an explicit annotation naming
the behavioral complement, instead of letting greps masquerade as
behavioral verification.

## Requirements

- R1: `docs/memory/anchored-acceptance-criteria.md` gains (a) a fourth
  failure pattern, the trivially satisfiable criterion — anchored per the
  existing doctrine yet green-checkable by typing the searched literal —
  with the surveyed examples above, and (b) a named criterion depth
  ladder: L0 text-presence (grep/count), L1 artifact-structure
  (existence, diff-shape, committed-file layout), L2 behavior (a command
  exercises the requirement's behavior: test run, script execution,
  produced-binary invocation), L3 end-to-end (eval scenario or user-flow
  walk). Rule: each requirement carries the deepest feasible criterion;
  a requirement whose criteria are all L0/L1 carries an explicit depth
  ceiling annotation stating why deeper is infeasible and naming the
  behavioral complement (an eval scenario, a manual-pending human read,
  or a named verifier judgment instruction).
- R2: `/idea`'s existing anchoring step (SKILL.md step 4) additionally
  classifies each drafted criterion's ladder level and applies R1's
  deepest-feasible rule at draft time, citing the memory doc.
- R3: `/breakdown` applies the same rule to task `## Acceptance`
  sections, citing the memory doc (its existing version-bump/mirror
  criterion guidance stays as-is).
- R4: `.claude/agents/critic.md`'s spec-review charter gains an
  acceptance-criteria attack checklist: for each criterion, (a) could a
  worker green-check it by writing the searched literal without
  implementing the requirement's behavior, (b) does the expected result
  still differ from current on-disk state (re-run the anchor check), and
  (c) does the spec end with at least one L2+ (or ceiling-annotated)
  check per behavioral requirement? A gameable criterion with no depth
  ceiling annotation blocks READY with the same force as an unmapped
  requirement. `.claude/skills/critique/SKILL.md`'s triage list names
  the gameable-criterion finding as JUDGMENT-class (a rewrite decision,
  not a mechanical patch).
- R5: `.claude/agents/verifier.md`'s verdict format gains a mandatory
  criteria-adequacy line: for each requirement, state whether the
  criteria that passed actually entail the requirement, and flag any
  behavioral requirement whose only green evidence is L0. A behavioral
  requirement evidenced solely by text-presence is INCOMPLETE, not PASS
  (prose requirements under a recorded depth ceiling annotation are
  exempt — that is the annotation's purpose).
- R6: one committed adversarial eval scenario for `/critique`:
  `evals/critique/02-gameable-criterion/` seeds a fixture spec whose one
  grep criterion is anchored (phrase absent from the fixture) but
  trivially satisfiable by its own requirement's literal; `assert.sh`
  asserts the critique run does NOT set `Breakdown-ready: true` and that
  its findings identify that criterion. The paid `./evals/run.sh
critique` run is manual-pending (human-launched — a drained worker
  cannot launch it, per docs/memory/unattended-worker-tool-limits.md);
  the committed scenario files are the drain-completable half.
- R7: mirrors and distribution: the antigravity ports of the idea,
  critique, and breakdown skills and of the critic/verifier agent→skill
  ports receive the equivalent edits (codex picks these up via its
  symlink overlay — none of the three codex real-content wrappers are
  touched); `.claude-plugin/plugin.json` `version` is bumped. Some
  task's `Touch:` lists all of these paths.

## Out of scope

- Rewriting existing specs' criteria to the ladder — they are graded on
  the doctrine in force when authored; the ladder applies to new specs
  and to specs revised for other reasons.
- Automated (hook/lint) detection of gameable criteria — gameability is
  a judgment call; this spec places it with the critic, not a grep.
- The eval-coverage tier policy and additional evalsets —
  `specs/eval-coverage-tiers`.

## Acceptance criteria

- [ ] `grep -ci 'depth ladder' docs/memory/anchored-acceptance-criteria.md`
      ≥ 1 and `grep -ci 'trivially satisfiable'
    docs/memory/anchored-acceptance-criteria.md` ≥ 1 (R1; both phrases
      absent today across all target files, verified 2026-07-19). Depth
      ceiling: doctrine prose — behavioral complement is R6's eval
      scenario plus the critic/verifier procedure greps below.
- [ ] `grep -c 'depth ceiling' .claude/skills/idea/SKILL.md` ≥ 1 and
      `grep -c 'depth ceiling' .claude/skills/breakdown/SKILL.md` ≥ 1,
      each within the file's acceptance-criteria authoring section and
      citing the memory doc rather than restating the ladder — cite-check
      by eyeball at review, grep is the anchor (R2, R3; phrase absent
      today, verified 2026-07-19).
- [ ] `grep -ci 'gameable' .claude/agents/critic.md` ≥ 1 and
      `grep -ci 'gameable' .claude/skills/critique/SKILL.md` ≥ 1 (R4;
      absent today, verified 2026-07-19).
- [ ] `grep -c 'criteria-adequacy' .claude/agents/verifier.md` ≥ 1 (R5;
      absent today, verified 2026-07-19).
- [ ] `[ -d evals/critique/02-gameable-criterion ] && grep -q
    'Breakdown-ready' evals/critique/02-gameable-criterion/assert.sh`
      (R6 — committed-scenario half; the passing run is manual-pending,
      paid headless, human-launched).
- [ ] The closing task's own commit modifies the plugin version line:
      `git show <closing-commit> -- .claude-plugin/plugin.json | grep -q
    '^+.*"version"'` (R7, per the memory doc's version-bump pattern);
      antigravity mirror greps for 'depth ceiling' and 'gameable' in the
      ported files ≥ 1 each (R7).

## Open questions

- Should R5's INCOMPLETE-on-L0-only rule bind retroactively when a
  verifier re-checks an old task after a relaunch, or only for specs
  authored after this lands? (Proposal: only new specs — same
  grandfathering as Out of scope bullet 1.)
- Is JUDGMENT the right class for R4's gameable-criterion finding, or
  should a criterion whose fix is obvious (swap doctrine-word grep for
  the procedure's decision-condition phrase) be MECHANICAL? (Proposal:
  JUDGMENT — the fix changes what the spec verifies, which is a
  spec-meaning change.)

## Parallelization

R1 is the foundation (the doctrine text the other edits cite). R2+R3
(authoring skills), R4 (critic + critique), R5 (verifier), R6 (eval
scenario) are then disjoint in Touch and can run concurrently. R7 closes.

- Group: R2+R3, R4, R5, R6
