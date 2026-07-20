Status: draft
Discovered-from: specs/eval-coverage-tiers/tasks/02-prioritize-evalset.md
Spec: ../SPEC.md
Blocking: no

# evals/run.sh should provision shared skill deps for every scenario

run.sh copies only the skill under test into the scenario sandbox, so any
skill whose scripts import sibling dirs (`.claude/skills/_shared`,
`.claude/skills/workboard`, `runtimes/`) crashes unless each scenario's
setup.sh hand-copies them — per-scenario boilerplate the prioritize
evalset (task 02) now carries. Provisioning `_shared` + `runtimes/` (and
script-dep skills) centrally in run.sh would remove it. (Worker-reported
discovery; vet/rewrite before promoting.)

## Acceptance

<!-- draft: needs runnable criteria before promotion -->
