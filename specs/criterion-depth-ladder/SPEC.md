# Criterion depth ladder: anti-gaming gates for acceptance criteria

Status: open
Breakdown-ready: true

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
positioned to catch this fire wrong: the critic attacks criteria
_presence_ but not depth — `.claude/agents/critic.md` blocks READY on
unmapped/missing criteria yet has no gameability/depth instruction, and
`.claude/skills/critique/SKILL.md` triages only "non-deterministic or
under-scoped" commands as MECHANICAL — and the
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
  requirement. `.claude/skills/critique/SKILL.md`'s triage list gains
  the verbatim sentence "gameable criteria are JUDGMENT-class, never
  MECHANICAL" inside its JUDGMENT enumeration — placement matters
  because the existing MECHANICAL bullet's "under-scoped acceptance
  command" reads adjacent, and the edit must not leave gameability
  claimable under that bullet. Rationale: even when the rewrite looks
  obvious, swapping what a criterion checks changes what the spec
  verifies — a spec-meaning change, never a mechanical patch. (Decided
  here; not an open question.)
- R5: `.claude/agents/verifier.md`'s verdict format gains a mandatory
  criteria-adequacy line: for each requirement, state whether the
  criteria that passed actually entail the requirement, and flag any
  behavioral requirement whose only green evidence is L0. A behavioral
  requirement evidenced solely by text-presence is INCOMPLETE, not PASS
  (prose requirements under a recorded depth ceiling annotation are
  exempt — that is the annotation's purpose). Binding scope is
  self-detecting, needing no external list: the rule binds any
  NOT-done spec whose acceptance sections carry the markers the ladder
  keys on
  (a `Depth ceiling:` line or a "verified <date>" anchor note) — which
  covers all specs authored after this lands and the specs the
  already-landed 2026-07-19 maintainer-directed sweep annotated (four
  remediation sweep commits on this same PR branch, plus the separate
  grandfathering-narrowing commit; the sweep is COMPLETED WORK this
  spec depends on, not a deliverable of any task here). Done/archived
  work is exempt unconditionally — pre-ladder anchoring notes
  ("verified <date>" predates the ladder) must not re-bind it — and
  gets ladder levels reported informationally without flipping the
  verdict, matching Out of scope bullet 1. (Decided; maintainer
  override 2026-07-19.)
- R6: one committed adversarial eval scenario for `/critique`:
  `evals/critique/02-adv-gameable-criterion/` (the `NN-adv-*` naming
  matches the adversarial-scenario convention proposed in
  `specs/eval-coverage-tiers`, so the two specs compose) seeds a fixture
  spec whose one grep criterion is anchored (phrase absent from the
  fixture) but trivially satisfiable by its own requirement's literal;
  `assert.sh` asserts BOTH halves: the critique run does NOT set
  `Breakdown-ready: true`, AND the persisted findings artifact
  (`critique-findings.md`, written on NOT READY per
  `.claude/skills/critique/SKILL.md`) identifies the seeded criterion.
  The paid `./evals/run.sh
critique` run is manual-pending (human-launched — a drained worker
  cannot launch it, per docs/memory/unattended-worker-tool-limits.md);
  the committed scenario files are the drain-completable half.
- R7: mirrors and distribution: the antigravity ports of the idea and
  breakdown skills, the critique workflow
  (`antigravity/.agents/workflows/critique.md`), and the
  critic/verifier agent→skill ports receive the equivalent edits
  (codex picks these up via its
  symlink overlay — none of the three codex real-content wrappers are
  touched); `.claude-plugin/plugin.json` `version` is bumped. Some
  task's `Touch:` lists all of these paths.

## Out of scope

- Rewriting DONE or archived specs' criteria to the ladder — completed
  work is graded on the doctrine in force when authored. (Narrowed by
  maintainer override, 2026-07-19: unimplemented specs — pending,
  draft, or not yet broken down — were ALREADY remediated in a
  one-time sweep, landed as four remediation sweep commits (plus the
  separate grandfathering-narrowing commit) on this PR branch before
  this spec's critique settled; the sweep is not a task of this spec,
  and only completed work is grandfathered.)
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
      `grep -c 'depth ceiling' .claude/skills/breakdown/SKILL.md` ≥ 1
      and `grep -c 'ladder level' .claude/skills/idea/SKILL.md` ≥ 1 and
      `grep -c 'ladder level' .claude/skills/breakdown/SKILL.md` ≥ 1 —
      both halves of the instruction (classification AND ceiling), each
      within the file's acceptance-criteria authoring section and
      citing the memory doc rather than restating the ladder (R2, R3;
      all four counts 0 today, verified 2026-07-19). Depth ceiling: prose
      authoring instruction — behavioral complement is the idea-evalset
      adversarial scenario proposed in `specs/eval-coverage-tiers` (a
      freshly authored SPEC must contain no unanchored/gameable
      criterion), plus a manual-pending human read of the edited
      sections at review.
- [ ] `grep -ci 'gameable' .claude/agents/critic.md` ≥ 1 and
      `grep -c 'JUDGMENT-class, never MECHANICAL'
.claude/skills/critique/SKILL.md` ≥ 1 — the mandated verbatim
      sentence encodes the placement, so appending "gameable" to the
      MECHANICAL bullet cannot pass (R4; both anchors 0 today, verified
      2026-07-19). Depth ceiling: prose charter —
      behavioral complement is R6's eval scenario, which exercises the
      critic actually flagging a seeded gameable criterion.
- [ ] `grep -c 'criteria-adequacy' .claude/agents/verifier.md` ≥ 1 (R5;
      absent today, verified 2026-07-19). Depth ceiling: prose charter —
      behavioral complement is a manual-pending human read of the first
      post-change verifier verdict, confirming the criteria-adequacy
      line appears per requirement and is non-vacuous.
- [ ] `bash -n evals/critique/02-adv-gameable-criterion/assert.sh &&
grep -q 'Breakdown-ready'
evals/critique/02-adv-gameable-criterion/assert.sh && grep -q
'critique-findings'
evals/critique/02-adv-gameable-criterion/assert.sh && grep -Eq
'exit 1|fail' evals/critique/02-adv-gameable-criterion/assert.sh`
      — committed-scenario SHAPE check, honestly L1: syntax-valid and
      the expected content/failure constructs present, though a
      comment-only stub could still satisfy the greps. The functional
      assert is proven only by the paid run (manual-pending,
      human-launched) — that run, not this shape check, is R6's
      behavioral half.
- [ ] Per-file mirror anchors (single-phrase-across-files lets a partial
      port pass, per the memory doc's multi-file rule):
      `grep -c 'depth ceiling' antigravity/.agents/skills/idea/SKILL.md`
      ≥ 1; `grep -c 'depth ceiling'
antigravity/.agents/skills/breakdown/SKILL.md` ≥ 1;
      `grep -ci 'gameable' antigravity/.agents/skills/critic/SKILL.md`
      ≥ 1; `grep -ci 'gameable' antigravity/.agents/workflows/critique.md`
      ≥ 1; `grep -c 'criteria-adequacy'
antigravity/.agents/skills/verifier/SKILL.md` ≥ 1 (R7; all five
      phrases absent from these ports today, verified 2026-07-19). The
      closing task's own commit modifies the plugin version line:
      `git show <closing-commit> -- .claude-plugin/plugin.json | grep -q
'^+.*"version"'` (R7, per the memory doc's version-bump pattern).

## Open questions

(none — the grandfathering and finding-class decisions are folded into
R4/R5.)

## Parallelization

Task 01 (doctrine) is the foundation the others cite. Tasks 02
(idea+breakdown), 03 (critic+critique), 04 (verifier), and 05 (eval
scenario) are disjoint in Touch and share no undecided design — the
ladder, the verbatim sentences, and the scenario name are all pinned
above — so they run concurrently once 01 lands (05 depends on nothing
and may start immediately). Task 06 (mirrors + version bump) closes.
Group grammar per specs/drain-rolling-window/SPEC.md's Parallelization
section.

- Group: 02, 03, 04, 05
