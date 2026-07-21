# eval-coverage-tiers — spec-completion review

spec review: 0 findings, 0 fixed, 1 discovered

Ref range reviewed: `f9778021fffd610c79304d445ab9cf463de2d7ec..6a0b7ba4c704190b9259b2583378d74941310f0f`
(the spec's first `Status: in-progress` flip commit through the last
merged task — all 8 tasks done, ~1500 product lines, mostly new eval
scenario dirs plus tier-policy docs).

## Coverage

- All 17 `assert.sh` graders reviewed (deep read of each grader + its
  sibling `prompt.txt`/`setup.sh`): no vacuous-pass, no
  pattern-also-matches-wrong-behavior, no dead reference, no
  setup/prompt/assert mismatch.
- `harness-audit/SKILL.md`'s tier-aware rewrite confirmed identically
  mirrored into the antigravity port (procedural parity intact).
- `evals` coverage-policy doc additions confirmed consistently mirrored
  across `.claude`, codex, and antigravity; relative links resolve from
  source-runtime depth.
- `COVERAGE.md` verified complete against the tree: all 22
  `.claude/skills/[!_]*` dirs present exactly once; all 11 Tier A skills
  have >=2 scenarios including one `NN-adv-*`; Tier B named tests exist.
- `plugin.json` version bump (0.9.21 -> 0.9.29 across the spec's life)
  confirmed monotonic.

## Discovered (uncertain, not fixed)

`evals/idea/02-adv-doctrine-grep/assert.sh` greps its anchor markers
(`verified <date>`, `Depth ceiling:`) across the whole produced spec file
rather than scoping to the specific criterion under test — a run keeping
a bad unanchored criterion but placing those markers elsewhere could
pass. Judged low-confidence (the subject under test is the real `/idea`
skill, not a string-gaming adversary), so not auto-fixed. Materialized as
`specs/eval-coverage-tiers/tasks/11-idea-adv-doctrine-grep-unanchored-marker-scope.md`
(`Status: draft`, `Blocking: no`).

## Known, out-of-scope, already-tracked issue (not re-fixed)

`tests/test_eval_coverage_lint.sh` / `evals/lint-eval-coverage.sh` use
`declare -A` (bash 4+) and fail/vacuously-pass under this host's macOS
system bash 3.2. Already tracked as draft stub 09
(`09-lint-vacuous-pass-missing-skills-dir.md`'s sibling issue, discovered
by task 07/08's workers) — not re-discovered or re-fixed here.

Gates: `evals/runner-selftest.sh` OK; `evals/lint-skill-size-gate.sh` OK;
`tests/test_mirror_procedure_coverage.sh` clean; `claude plugin validate .`
passed; `specs/status.sh` runs.
