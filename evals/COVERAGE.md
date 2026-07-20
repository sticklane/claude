# Eval coverage tiers

Which of the toolkit's skills need an evalset, and which are deliberately
covered another way. Every `[!_]*` directory under `.claude/skills/` (i.e.
every skill; `_shared` is a shared-asset dir, not a skill) appears exactly
once below. `evals/lint-eval-coverage.sh` enforces this table against the
tree — a new skill missing a row, a Tier A skill under its scenario bar, a
Tier B row naming an absent test, or a Tier C row with no reason all fail
the lint. Run it directly (`bash evals/lint-eval-coverage.sh`); it is never
wired into `evals/run.sh`, which spawns paid model sessions.

The tiers:

- **Tier A — paid evalset required.** Queue-state-mutating or dispatch-heavy
  pipeline skills. Bar: ≥2 scenario dirs (each containing `setup.sh`,
  `prompt.txt`, and `assert.sh`), at least one adversarial — a scenario whose
  correct outcome is to refuse, flag, or not act, named `NN-adv-*`.
- **Tier B — model-free tests instead.** Deterministic-core reporting skills;
  the named test file(s) stand in for a paid run, and the lint checks they
  exist.
- **Tier C — waived, reason recorded.** Skills not hermetically evalable
  today (session-runtime state, non-hermetic network) or deferred to a later
  round; each row states why.

This table is the mechanism; the rows are the current call. A human may amend
rows — that is an edit to this file, not a blocker. Amending a Tier A skill
to a met bar, or a Tier C waiver to a Tier B test, is how coverage grows.

| Skill           | Tier | Bar / reason                                                                                                                       | Tier B tests                                 |
| --------------- | ---- | ---------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------- |
| breakdown       | A    | ≥2 scenarios, ≥1 adversarial (NN-adv-\*)                                                                                           |                                              |
| build           | A    | ≥2 scenarios, ≥1 adversarial (NN-adv-\*)                                                                                           |                                              |
| critique        | A    | ≥2 scenarios, ≥1 adversarial (NN-adv-\*)                                                                                           |                                              |
| distill         | A    | ≥2 scenarios, ≥1 adversarial (NN-adv-\*)                                                                                           |                                              |
| drain           | A    | ≥2 scenarios, ≥1 adversarial (NN-adv-\*)                                                                                           |                                              |
| evals           | A    | ≥2 scenarios, ≥1 adversarial (NN-adv-\*)                                                                                           |                                              |
| gate            | A    | ≥2 scenarios, ≥1 adversarial (NN-adv-\*)                                                                                           |                                              |
| idea            | A    | ≥2 scenarios, ≥1 adversarial (NN-adv-\*)                                                                                           |                                              |
| onboard         | A    | ≥2 scenarios, ≥1 adversarial (NN-adv-\*); artifact-only assertions (assert what the run writes and must NOT write)                 |                                              |
| prioritize      | A    | ≥2 scenarios, ≥1 adversarial (NN-adv-\*); colocated test_prioritize_scan.py is supplementary                                       |                                              |
| list-specs      | B    | deterministic core; model-free test in lieu of a paid run                                                                          | .claude/skills/list-specs/test_list_specs.py |
| workboard       | B    | deterministic core; model-free test in lieu of a paid run                                                                          | .claude/skills/workboard/test_workboard.py   |
| design          | C    | waived: pending a later round                                                                                                      |                                              |
| factcheck       | C    | waived: non-hermetic network flow, not hermetically evalable                                                                       |                                              |
| fleet           | C    | waived: reads live session-runtime state, not hermetically evalable                                                                |                                              |
| handoff         | C    | waived: pending a later round (the handoff/resume round-trip is the named candidate)                                               |                                              |
| harness-audit   | C    | waived: a prose checklist with no deterministic core module today (promotion candidate if its mechanics get extracted to a script) |                                              |
| prose-review    | C    | waived: pending a later round                                                                                                      |                                              |
| qa-sweep        | C    | waived: non-hermetic network flow, not hermetically evalable                                                                       |                                              |
| resume-handoff  | C    | waived: pending a later round (the handoff/resume round-trip is the named candidate)                                               |                                              |
| workflow-author | C    | waived: pending a later round                                                                                                      |                                              |
