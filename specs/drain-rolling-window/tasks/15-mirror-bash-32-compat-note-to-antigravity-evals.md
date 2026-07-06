Status: draft
Discovered-from: 11-evals-runner-bash-32-compat-note.md
Spec: ../SPEC.md
Blocking: no

# Mirror the bash-3.2 compat note into the antigravity evals workflow

Task 11 added a one-line "macOS system bash is 3.2, no `declare -A`" compat
note to `.claude/skills/evals/reference.md` and a matching comment at the
top of `evals/run.sh`. `antigravity/.agents/workflows/evals.md` (the
antigravity mirror) documents authoring `setup.sh`/`assert.sh` scenario
scripts too but carries no equivalent warning. Per CLAUDE.md's mirroring
convention, port the same one-line note into that file.

## Acceptance

<!-- draft: needs runnable criteria before promotion -->
