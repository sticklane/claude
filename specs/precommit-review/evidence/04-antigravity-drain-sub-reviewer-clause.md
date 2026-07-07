Verdict: PASS

Criterion 1 — grep passes
Command: `grep -q 'sub-reviewer' antigravity/.agents/workflows/drain.md`
Result: exit 0 (confirmed via `grep -n 'sub-reviewer' -i antigravity/.agents/workflows/drain.md` → line 142: "procedure spawns a simplification, cleanup, or review sub-reviewer as").

Criterion 2 — clause placement and semantic fidelity
Command: `Read antigravity/.agents/workflows/drain.md` lines 120-159 (worker dispatch prompt blockquote).
Evidence: lines 141-147 read: "If the build procedure spawns a simplification, cleanup, or review sub-reviewer as a separate background agent, do NOT block waiting on a notification from it — a sub-agent's result may not route back to you. Run that pass inline, or if you fan it out, read its output directly rather than awaiting a notification, then finish close-out and deliver your verdict." — this sits inside the `>` blockquote worker-dispatch prompt (same block as the "Budget:" and "worktree disappears mid-run" clauses), and is semantically faithful to `.claude/skills/drain/reference.md` lines 328-333 (same instruction: don't block on background sub-reviewer notification, run inline or read output directly, then finish close-out and deliver verdict).

Criterion 3 — only the mirror file changed
Command: `git diff de9ce61 --stat`
Result:
```
 antigravity/.agents/workflows/drain.md | 8 +++++++-
 1 file changed, 7 insertions(+), 1 deletion(-)
```
Confirms the only working-tree change relative to base is `antigravity/.agents/workflows/drain.md`.

Criterion 4 — task file append-only / untouched
Command: `git diff de9ce61 -- 'specs/precommit-review/tasks/*.md'`
Result: empty diff — the task file is byte-identical to base (Status: in-progress was already committed at base; the acceptance checkbox is still unticked, matching the stated expectation that the worker had not yet flipped status/ticked the box).

Scope creep: none — `git status --short` shows only `M antigravity/.agents/workflows/drain.md` as a tracked change matching this task's scope; other unrelated modified files listed in the outer git status belong to prior/unrelated work in this worktree, not this task's diff (verified via `git diff de9ce61 --stat` above, which shows a single-file diff).

Gates: no build/lint/test gate applies to this doc-only mirror edit; `bash evals/lint-ultra-gate.sh` not applicable (drain.md is not one of the four ultra-path skill files under `.claude/skills/`, and no "ultra" text was touched).
