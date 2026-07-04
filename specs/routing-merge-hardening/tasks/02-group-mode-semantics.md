# Task 02: Drain group-mode sequencing, gate-failure stop, push-guard wording

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers. ## Progress / ## Deferred questions are drain-written sections. -->

Status: pending
Depends on: none
Priority: P2
Budget: 8 turns
Spec: ../SPEC.md (F3, F4, F5)
Touch: .claude/skills/drain/SKILL.md, antigravity/.agents/workflows/drain.md, .claude-plugin/plugin.json

## Goal

Drain's group throughput mode is unambiguous about lock/commit sequencing
(one batched status-flip commit, one launch message, wait for all
completions), stops on post-merge gate failures during group integration
(restoring retired /parallel's behavior), and the push-guard parenthetical
no longer cites the retired /parallel skill. Step 2's heading no longer
says "one worker" while describing group dispatch. Antigravity drain
mirror matches. Plugin version bumped (skill behavior change).

## Steps

1. In `.claude/skills/drain/SKILL.md`: retitle `## 2. Dispatch one worker`
   to `## 2. Dispatch` (or similar covering both modes).
2. In the group throughput mode paragraph, add the explicit sequence: flip
   every member's `Status: in-progress` and commit them in one commit; cut
   all member worktrees from that commit; launch all workers in one
   message; then wait for all completion notifications — collecting each
   verdict via step 3 as it arrives — before dispatching anything else.
3. Extend the group-mode stop rule: a post-merge gate failure during group
   integration also stops the remaining merges and reports (interaction
   effects between members are indistinguishable from the task's own
   failure at that point).
4. Reword "(canonical; build and parallel cite this)" — build cites it;
   drain's own group mode follows it.
5. Mirror 2–4 into `antigravity/.agents/workflows/drain.md` (group
   paragraph and its push-guard line; its step-2 heading if it has the
   same problem).
6. Bump `.claude-plugin/plugin.json` version (patch).

## Acceptance

- [ ] `grep -q 'one commit' .claude/skills/drain/SKILL.md` → exit 0
- [ ] `grep -q 'one commit' antigravity/.agents/workflows/drain.md` → exit 0
- [ ] `grep -q 'post-merge gate failure' .claude/skills/drain/SKILL.md` → exit 0
- [ ] `grep -q 'post-merge gate failure' antigravity/.agents/workflows/drain.md` → exit 0
- [ ] `! grep -rq 'build and parallel cite this' .claude antigravity` → exit 0
- [ ] `! grep -q '## 2. Dispatch one worker' .claude/skills/drain/SKILL.md` → exit 0
- [ ] `./bin/check-token-discipline && bash evals/lint-ultra-gate.sh` → exit 0
- [ ] `bash tests/test_check_token_discipline.sh` → pass, 0 fail
