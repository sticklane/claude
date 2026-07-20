Status: draft
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

<!-- draft: needs runnable criteria before promotion -->
