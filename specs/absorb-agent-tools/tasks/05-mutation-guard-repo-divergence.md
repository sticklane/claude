Status: in-progress
Depends on: none
Priority: P0
Budget: 16 turns
Discovered-from: specs/absorb-agent-tools/tasks/02-import-agent-console-deduped.md
Spec: ../SPEC.md
Touch: agent-console/agent-console.py, agent-console/tests/test_parsers.py
Blocking: no

# Mutation-guard repo list can diverge from the workboard's repo list

agent-console's mutation guard (`_tracked_repo_reals()`/`parse_repos()` at
`agent-console/agent-console.py:1407-1408,369-386`, reading `REPOS.md`)
gates `/api/priority` (line 1641) and `/api/agent/start` (line 1644) — NOT
the whole `/api/agent/*` family; `/api/agent/stop` and `/api/agent/resume`
don't gate on tracked repos at all, so correct that in the fix's
description, not just the acceptance checks. The Workboard tab's repo list
comes from `workboard.default_roots()`
(`.claude/skills/workboard/workboard.py:133-137`, walking `~/code`,
`~/src`, `~/projects`, `~/dev`, `~/repos`, `~/work`) — the two
repo-discovery sources can diverge, so a repo shown on the board can be
rejected by a priority-edit or agent-kickoff as "outside tracked repos"
(or vice versa).

## Steps

1. Change `_tracked_repo_reals()` to return the union of `parse_repos()`
   (REPOS.md) and `workboard.default_roots()`'s walk, so a repo visible in
   either source is accepted by both gated endpoints. Keep `parse_repos()`
   itself unchanged (other callers may rely on REPOS.md-only semantics) —
   union at the `_tracked_repo_reals()` call site.
2. Add a regression test to `agent-console/tests/test_parsers.py` that
   constructs a repo present only via a `default_roots()`-style path (not
   in `REPOS.md`) and confirms `/api/priority`/`start_agent` no longer
   reject it.

## Acceptance

- [ ] `cd agent-console && python3 -m pytest tests/test_parsers.py -v` → all pass, including the new divergence regression test
- [ ] A repo present in a `default_roots()`-style root but absent from `REPOS.md` is accepted by `_tracked_repo_reals()` (verified by the new test, not just by inspection)
- [ ] `grep -n 'def _tracked_repo_reals' agent-console/agent-console.py` shows it now reads from both `parse_repos()` and a `default_roots()`-equivalent walk (or a shared helper), not `parse_repos()` alone
