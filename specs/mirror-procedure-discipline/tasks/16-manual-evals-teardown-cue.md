Status: obsolete
Closed: 2026-07-13 (Steven, attended) — superseded by d2ae9ba: the manual steps-2–4 flow no longer exists (`agy -p --new-project` confirmed safe; the workflow drives evals/run.sh headlessly), and evals/run.sh itself runs teardown.sh whenever setup was attempted. The cue is structural, not operator-dependent.
Intake-refused: screen — instruction-shaped Goal matched: tool-invocation (2026-07-13)
Discovered-from: specs/mirror-procedure-discipline/tasks/04-audit-evals.md
Spec: ../SPEC.md
Blocking: no

# Add a teardown.sh cue to the manual Antigravity evals flow

`antigravity/.agents/workflows/evals.md`'s manual flow (steps 2-4, since
`agy -p` is live-tested unsafe for isolated/unattended use per
`runtimes/antigravity.md`) never names `teardown.sh`. An operator running
an eval that seeds external live-service state gets no cue to clean it up
after the session — the source `.claude/skills/evals/SKILL.md`'s automated
runner invokes teardown itself, but the manual mirror has no equivalent
step or reminder. Confirmed as a real gap by the task 04 evals audit, which
deliberately left it unfixed since it sits across the load-bearing boundary
(the manual-vs-automated split itself) and the audit's scope was to confirm
that split still holds, not to extend the manual flow.

## Acceptance

<!-- draft: needs runnable criteria before promotion -->
