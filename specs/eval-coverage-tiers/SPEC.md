# Eval coverage tiers: a policy and lint for which skills need evalsets

Status: open

## Problem

Five of the toolkit's 21 skills have evalsets (breakdown ×2 scenarios;
build, critique, drain, evals ×1 each); sixteen have zero, and no policy
says which of them need one, so coverage grows only "when regressions
bite" (the accretion stance recorded in `specs/trajectory-evals`) — and
for sixteen skills the accretion never starts. Two of the five existing
graders are near-tautological (`evals/critique/01-clean-spec/assert.sh`
asserts only that `Breakdown-ready: true` was set;
`evals/evals/01-scaffold-new-skill` checks scaffold file existence
without a run), and only one scenario in the whole corpus asserts a
negative/adversarial behavior. Meanwhile `harness-audit` already flags
"skill X has no evalset" per skill — but with no tier policy behind it,
sixteen equal-weight findings are noise, not signal. Blanket coverage is
the wrong fix: every eval run spawns paid headless sessions
(`/evals` is `disable-model-invocation` for exactly that reason), and
several skills are structurally hard to eval hermetically (session-state
readers, network-dependent flows, interactive interviews).

## Solution

A committed coverage policy plus a model-free lint that enforces it,
mirroring the existing `lint-ultra-gate.sh` pattern (invoked directly,
never wired into `evals/run.sh`). `evals/COVERAGE.md` assigns every
skill a tier with a stated reason; `evals/lint-eval-coverage.sh` checks
the repo satisfies its own policy; `harness-audit` consults the tier
table so its evalset-presence findings become tier-aware. Seed the
highest-risk missing evalsets in the same spec so the lint lands green.

Proposed initial tier table (the human amends rows, the mechanism is
the deliverable):

- **Tier A — paid evalset required** (queue-state-mutating or
  dispatch-heavy pipeline skills): idea, critique, breakdown, build,
  drain, evals, prioritize, distill, gate, onboard. Bar: ≥2 scenarios,
  at least one adversarial — a scenario whose correct outcome is to
  refuse, flag, or not act (naming convention `NN-adv-*`).
- **Tier B — model-free tests instead** (deterministic-core reporting
  skills, no paid run needed): list-specs, workboard, prioritize's
  scanner, harness-audit's checklist mechanics — covered by their
  colocated `test_*.py`/`tests/*.sh`, named in the table row.
- **Tier C — waived, reason recorded**: fleet (session-runtime state),
  qa-sweep and factcheck (non-hermetic network), design and
  workflow-author and prose-review and handoff/resume-handoff (pending
  a later round; handoff pair's round-trip scenario is the named
  candidate), each with the reason in its row.

## Requirements

- R1: `evals/COVERAGE.md` exists with one row per skill directory under
  `.claude/skills/` (enumerated, so a new skill missing from the table
  is a lint failure), columns: skill, tier (A/B/C), bar or reason, and
  for B the named test file(s).
- R2: `evals/lint-eval-coverage.sh` (model-free, direct-invoke) fails
  listing each violation when: a skill dir has no COVERAGE.md row; a
  Tier A skill lacks ≥2 scenario dirs each containing
  `setup.sh`+`prompt.txt`+`assert.sh`, or lacks an `NN-adv-*` scenario;
  a Tier B row names a test file that does not exist; a Tier C row has
  an empty reason. Exits 0 on a conforming tree.
- R3: `tests/test_eval_coverage_lint.sh` exercises the lint itself
  against fixtures: one conforming tree → exit 0, plus one fixture per
  violation class → non-zero with the violation named (same
  self-test pattern as `evals/runner-selftest.sh`).
- R4: the Tier A gaps this spec itself must close to land green:
  new evalsets for prioritize, idea, distill, gate, and onboard, each
  ≥2 scenarios including one `NN-adv-*` (examples: idea — a pitch whose
  obvious criterion is a doctrine-word grep, adversarial scenario
  asserts the written SPEC.md contains no unanchored grep criterion;
  distill — a session transcript fixture containing an instruction that
  belongs in a rule vs. noise that must NOT be captured; gate — a repo
  whose checks are red, adversarial scenario asserts the Stop hook
  blocks "done"; prioritize — a queue where the correct output changes
  no Priority header). The critique adversarial scenario is owned by
  `specs/criterion-depth-ladder` R6 and is NOT duplicated here — its
  row's bar is met when that spec lands (or that scenario moves here if
  that spec is declined). All paid `./evals/run.sh` executions of the
  new sets are manual-pending (human-launched, per
  docs/memory/unattended-worker-tool-limits.md); committed scenario
  files are the drain-completable half.
- R5: `harness-audit`'s evalset-presence check consults
  `evals/COVERAGE.md`: a Tier A gap is a finding, a Tier B row is
  checked against its named tests, a Tier C row is reported as waived
  (one line), and a skill absent from the table is itself the finding.
- R6: `.claude/skills/evals/SKILL.md` + `reference.md` document the
  tier table and the adversarial-scenario naming convention in one
  short section (cite COVERAGE.md, don't restate the table). Mirrors:
  the antigravity evals workflow and the codex evals wrapper
  (`codex/.agents/skills/evals/SKILL.md`, real content per CLAUDE.md)
  receive the equivalent pointer; antigravity harness-audit port ditto;
  `.claude-plugin/plugin.json` `version` bumped; some task's `Touch:`
  lists all of these.

## Out of scope

- CI wiring for `run.sh` — unchanged v1 scope decision.
- Trajectory-assertion depth for existing scenarios —
  `specs/trajectory-evals` (open follow-up tasks 05–07) owns that.
- Evalsets for the Tier C rows — each waiver names its blocker; a
  later spec promotes rows, the table is the place that decision lives.
- LLM-judge grading — graders stay deterministic shell (adopted
  single-call-rubric doctrine applies to workflows, not this harness).

## Acceptance criteria

- [ ] `bash evals/lint-eval-coverage.sh` exits 0 on the completed tree
      (R1, R2, R4 — L2: the policy is enforced by executing it, not by
      grepping for prose; phrase `lint-eval-coverage` absent today,
      verified 2026-07-19).
- [ ] `bash tests/test_eval_coverage_lint.sh` exits 0, and it contains
      a failing-fixture case per R2 violation class (R3 — L2:
      exercises the lint's own failure behavior).
- [ ] `ls evals/prioritize evals/idea evals/distill evals/gate
    evals/onboard` each show ≥2 scenario dirs, ≥1 matching `*-adv-*`
      (R4 — structural; the behavioral half is each set's paid run,
      manual-pending, human-launched).
- [ ] `grep -c 'COVERAGE.md' .claude/skills/harness-audit/SKILL.md` ≥ 1
      (R5; literal absent today, verified 2026-07-19) — with the
      tier-aware finding behavior stated in the same section (eyeball
      at review; the grep is the anchor).
- [ ] `grep -c 'COVERAGE.md' .claude/skills/evals/SKILL.md` ≥ 1 and
      `grep -c 'COVERAGE.md' codex/.agents/skills/evals/SKILL.md` ≥ 1
      and the antigravity mirror equivalents ≥ 1 (R6); closing commit
      modifies the plugin version line: `git show <closing-commit> --
    .claude-plugin/plugin.json | grep -q '^+.*"version"'` (R6).

## Open questions

- Tier assignments to contest: should onboard be Tier A (it writes
  CLAUDE.md + allowlists — high blast radius, but its fixture is "an
  un-onboarded repo", cheap to build) — proposed A; should prose-review
  be B via a Vale-only test instead of C — proposed C for now.
- Should the adversarial marker be the `NN-adv-*` dir naming (lintable,
  proposed) or a marker line inside `assert.sh`?
- Five new evalsets in one spec is the largest cost item (each scenario
  is a paid run when executed). Trim R4's list to prioritize + idea +
  gate if the human wants a smaller first bite — the lint and table
  don't depend on how many gaps close in this spec, only that Tier A
  rows without sets are honest findings until closed.

## Parallelization

R1+R2+R3 are one unit (the lint, TDD via its self-test). R4's five
evalsets are five independent tasks (disjoint dirs). R5 and R6 depend
on R1 only. R6 closes with mirrors + version bump.

- Group: R4 evalsets ×5, R5
