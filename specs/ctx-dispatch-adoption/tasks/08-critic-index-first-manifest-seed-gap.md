Status: obsolete
Closed: subsumed by specs/agentic-core-redesign — see specs/agentic-core-redesign/TRIAGE.md
Discovered-from: specs/ctx-dispatch-adoption/tasks/03-critic-grant-onboard-allowlist.md
Spec: ../SPEC.md
Blocking: no

# critic's "index-first: prefer ctx" phrase is unseeded in the mirror-procedure manifest

Task 03 added the phrase "index-first: prefer ctx" to both
`.claude/agents/critic.md` and `antigravity/.agents/skills/critic/SKILL.md`
(the mirror leg, deliberately without the `Bash(ctx` tools grant — a
load-bearing divergence). `tests/mirror-procedure-manifest.txt` — the
curated `<source>|<mirror>|<phrase>` list `test_mirror_procedure_coverage.sh`
greps — was not seeded with this phrase, since seeding it was outside
task 03's Touch. Without a manifest line, a future edit to either file
could silently re-drop the phrase from the mirror with no gate catching
it.

## Acceptance

<!-- draft: needs runnable criteria before promotion -->
