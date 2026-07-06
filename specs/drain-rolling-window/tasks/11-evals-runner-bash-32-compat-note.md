Status: done
Discovered-from: specs/drain-rolling-window/tasks/06-drain-eval-scenario.md
Spec: ../SPEC.md
Blocking: no

# evals/run.sh invokes assert/setup scripts with bare bash, but macOS ships bash 3.2 — no compatibility note anywhere

macOS's system `bash` is 3.2, and `evals/run.sh` invokes each scenario's `assert.sh`/`setup.sh` with bare `bash` (not requiring bash 4+). The task 06 worker hit this directly: an early `assert.sh` draft used `declare -A` (a bash-4-ism) and silently misbehaved under the runner's actual bash 3.2 invocation rather than erroring clearly. Future eval-scenario authors will rediscover this the hard way unless it's called out — e.g. a one-line compatibility note in `.claude/skills/evals/reference.md` or a comment in `evals/run.sh` itself.

Decision (2026-07-06): do BOTH (each is one line): a compat note in `.claude/skills/evals/reference.md` AND a comment at the top of `evals/run.sh`, each warning that macOS's system bash is "bash 3.2" — no `declare -A` or other bash-4+ syntax in scenario `assert.sh`/`setup.sh` scripts. Use the literal phrase "bash 3.2" so the checks below hold.

## Acceptance

- [x] `grep -q 'bash 3.2' .claude/skills/evals/reference.md` → exits 0 (compat note present; currently absent) — exits 0; compat note added to reference.md intro
- [x] `grep -q 'bash 3.2' evals/run.sh` → exits 0 (top-of-file comment present; currently absent) — exits 0; comment added to run.sh header block
