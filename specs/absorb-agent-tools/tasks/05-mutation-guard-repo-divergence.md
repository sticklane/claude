Status: draft
Discovered-from: specs/absorb-agent-tools/tasks/02-import-agent-console-deduped.md
Spec: ../SPEC.md
Blocking: no

# Mutation-guard repo list can diverge from the workboard's repo list

agent-console's mutation guard (`_tracked_repo_reals()`/`parse_repos()`, reading `REPOS.md`) still gates `/api/priority` and `/api/agent/*`, but the Workboard tab's repo list now comes from `workboard.default_roots()` (walks `~/code`, `~/src`, etc.) — the two repo-discovery sources can diverge, so a repo shown on the board might reject a priority-edit or agent-kickoff as "outside tracked repos."

## Acceptance

<!-- draft: needs runnable criteria before promotion -->
