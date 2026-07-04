# Task 05: Version bump + end-to-end dispatch-language check

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
Status: in-progress
Depends on: 03, 04, ../../ultra-mode/tasks/03-decision-record-bump-e2e.md
Priority: P2
Budget: 25 turns
Spec: ../SPEC.md (requirement R7-bump, end-to-end)
Touch: .claude-plugin/plugin.json, specs/workflow-token-efficiency/evidence/

## Goal

plugin.json gets the spec's single version bump, and the end-to-end check
is recorded: a fresh session invoking `/parallel` on a two-task toy list
produces dispatch prompts containing the tier and output-budget language,
observed in the dispatch text before workers run.

## Steps

1. Bump plugin.json minor version once; `claude plugin validate .`.
2. E2e: build a two-task toy list (temp fixture), invoke a fresh session
   (`claude -p` or a subagent given only the parallel SKILL.md) far
   enough to emit its dispatch prompts, capture the prompts, and assert
   tier + output-budget language is present; record the capture in
   specs/workflow-token-efficiency/evidence/05-e2e.md. Do not let toy
   workers actually execute against the repo.
3. Full-suite sanity: `bin/check-token-discipline` exit 0,
   `bash tests/test_check_token_discipline.sh` exit 0,
   `bash tests/test_sync_workflows.sh` exit 0,
   `bash evals/lint-ultra-gate.sh` exit 0.

## Acceptance

- [ ] `git diff HEAD~1 -- .claude-plugin/plugin.json` in the implementing commit shows one version bump; `claude plugin validate .` → exit 0
- [ ] Evidence file shows captured /parallel dispatch prompts containing tier and output-budget language before any worker ran
- [ ] All four suite commands above → exit 0
