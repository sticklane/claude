# Evidence: task-priority 02-research-record

Verified: 2026-07-03
Branch: task/02-research-record
Verdict: PASS

## Criterion 1 — task-file acceptance command (R4 grep)

Command (run in worktree root):

```
grep -qi "task prioritization" docs/external-playbooks.md && \
  sed -n '/[Tt]ask prioritization/,/^## /p' docs/external-playbooks.md | grep -qi "ready set"
```

Output: `exit=0` — PASS. (The "Task prioritization" section is the last
section of the file; the sed range runs to EOF, which is correct here.)

## Criterion 2 — R4 content requirements

Checked the appended "## Task prioritization" section (docs/external-playbooks.md,
lines 274-309 of the working tree; 37-line addition) against SPEC.md R4:

- Convergence bullet "dependency graph → ready set → waves": present. ✓
- Six pinned URLs, all present verbatim in the entry:
  - https://kiro.dev/docs/specs/best-practices ✓
  - https://github.blog/ai-and-ml/github-copilot/run-multiple-agents-at-once-with-fleet-in-copilot-cli/ ✓
  - https://adk.dev/agents/workflow-agents/ ✓
  - https://jules.google/docs/usage-limits/ ✓
  - https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents ✓
  - https://developers.openai.com/cookbook/articles/codex_exec_plans ✓
- Gap bullet: "No vendor publishes a rule for which ready task goes
  first ... toolkit's Priority → unblocking-power → path tie-break is
  therefore ahead of published guidance" — matches R4's
  no-vendor-ranking gap. ✓
- Adopted signal 1 (Anthropic): "choose the highest-priority feature
  that's not yet done", one at a time, priority pre-assigned →
  `Priority:` header + sequential dispatch. ✓
- Adopted signal 2 (OpenAI): PLANS.md PoC-milestones-first as
  risk-first ordering → /breakdown P0 rubric. ✓
- Jules "planned" queue prioritization and ADK
  mechanisms-not-heuristics detail both present. ✓

## Criterion 3 — scope

Command: `git diff main --stat` and `git status --porcelain`

```
 docs/external-playbooks.md | 37 +++++++++++++++++++++++++++++++++++++
 1 file changed, 1 insertion block (append-only at EOF)
 M docs/external-playbooks.md   (only modified file; no untracked files)
```

Matches the task's Touch list exactly (docs/external-playbooks.md,
appender). No plugin.json bump, no mirror edits, no other files — no
scope creep. ✓

## Gates

Docs-only change: no build/lint/test gates apply. No skill, agent, or
eval files were modified (evals/run.sh precondition not triggered). No
test files exist for this criterion to overfit against; the appended
prose is real research content, not grep-bait (marker phrases appear
inside substantive bullets with correct source links).

## Notes (non-blocking)

- Task file Status is still `in-progress` and the acceptance checkbox
  unchecked — bookkeeping for the orchestrator to flip on merge; the
  user's instructions allow task-file bookkeeping and none was needed
  to pass.
