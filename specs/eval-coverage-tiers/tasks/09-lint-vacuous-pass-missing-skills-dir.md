Status: done
Touch: evals/lint-eval-coverage.sh, tests/test_eval_coverage_lint.sh, specs/eval-coverage-tiers/tasks/09-lint-vacuous-pass-missing-skills-dir.md
Discovered-from: specs/eval-coverage-tiers/tasks/01-coverage-table-and-lint.md
Spec: ../SPEC.md
Blocking: no

# lint-eval-coverage.sh passes vacuously when .claude/skills is missing or empty

`shopt -s nullglob` plus the skill-enumeration loop `for d in
"$SKILLS_DIR"/[!_]*/;` makes the whole lint pass vacuously when
`.claude/skills` doesn't exist or has no matching entries under
`$ROOT`/`LINT_ROOT`: the glob expands to zero paths, the only
violation-reporting loop never runs, and the script prints "OK" and exits
0 despite checking nothing — while the analogous missing-`COVERAGE.md`
case IS guarded (exit 1). Add a `$SKILLS_DIR` existence/non-emptiness
guard and a self-test fixture. (Reported by the dispatch's code-review
pass; vet/rewrite before promoting.)

## Acceptance

The guard is placed above the lint's bash-4 `declare -A` table parse, so it is
exercisable on its own even where only bash 3.2 is installed; the full
self-test (cases 0–5) needs bash 4+ as the lint has always required.

- [x] The lint fails (exit 1, message names `no skill dirs`) when `.claude/skills`
      is absent under `LINT_ROOT` but `evals/COVERAGE.md` exists — no vacuous
      pass. Verified: `mkdir -p $T/evals && printf ... > $T/evals/COVERAGE.md;
      LINT_ROOT=$T bash evals/lint-eval-coverage.sh` → `rc=1`, output
      `lint-eval-coverage: FAIL — no skill dirs under .../.claude/skills`.
- [x] The lint fails the same way when `.claude/skills` exists but holds no
      `[!_]*` entry (only `_shared`). Verified: same command with
      `mkdir -p $T/.claude/skills/_shared` → `rc=1`, same `no skill dirs` message.
- [x] A populated skills dir still reaches the enumeration loop — the guard does
      NOT fire and short-circuit. Verified: patched lint against the real tree
      (23 `[!_]*` skill dirs) does not print `no skill dirs`; execution proceeds
      past the guard to the table-parse step.
- [x] `tests/test_eval_coverage_lint.sh` carries a fixture case for each new
      violation shape (absent skills dir; `_shared`-only skills dir), each
      asserting non-zero exit with `no skill dirs` named — running the whole
      self-test on bash 4+ exits 0.
