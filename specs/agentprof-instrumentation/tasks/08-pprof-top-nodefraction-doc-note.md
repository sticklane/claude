Status: draft
Discovered-from: specs/agentprof-instrumentation/tasks/04-e2e-duration-evidence.md
Spec: ../SPEC.md
Blocking: no

# Document that go tool pprof -top's default node-fraction pruning hides small tool: frames

`go tool pprof -top`'s default node-fraction pruning hides `tool:` frames on real day-scale profiles (each tool call's individual duration is tiny relative to the total span across all projects), so the plain command shows zero `tool:` lines even though the data is present and correct — `-nodefraction=0 -edgefraction=0` (or a narrower `--days`/project filter) is needed to see them. Worth a one-line note in agentprof's own docs or `agentprof/README.md` so a future human running this command by hand doesn't conclude the feature is broken.

## Acceptance

<!-- draft: needs runnable criteria before promotion -->
