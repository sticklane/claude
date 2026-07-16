# Verification evidence: specs/trajectory-evals/tasks/03-docs-and-codex-mirror.md

Verdict: PASS

Base commit for task-file diff: 620650636b2fa553dea6c4f240dc83c72b519dd1
Branch verified: task/03-docs-and-codex-mirror

## Task-file append-only check

`git diff <base> -- specs/trajectory-evals/tasks/03-docs-and-codex-mirror.md`
shows only a `<!-- PLAN (build) ... -->` comment block inserted after the
header fields. Status line ("in-progress"), Goal/Steps/Touch/Budget, and all
acceptance-criteria text are byte-identical to base. No checkbox was ticked,
no evidence line was added — the only change is the plan comment block,
which is within the permitted set. (Note: since no boxes are ticked and
Status was left as "in-progress" rather than moved to a completed state,
this task file does not itself claim completion — the underlying file
changes were still verified directly below.)

## Six acceptance commands (run verbatim from ## Acceptance)

```
$ grep -q "EVAL_TRANSCRIPT" .claude/skills/evals/SKILL.md          → exit 0  PASS
$ grep -q "EVAL_TRANSCRIPT" .claude/skills/evals/reference.md      → exit 0  PASS
$ ! grep -q "v1 grades artifacts only" .claude/skills/evals/SKILL.md → exit 0  PASS
$ grep -q "EVAL_TRANSCRIPT" codex/.agents/skills/evals/SKILL.md    → exit 0  PASS
$ ! grep -q "v1 grades artifacts only" codex/.agents/skills/evals/SKILL.md → exit 0  PASS
$ grep -q "never a transcript" codex/.agents/skills/evals/SKILL.md → exit 0  PASS
```

All six PASS.

## Task-specific correctness checks

1. **v1/v2 reframe in `.claude/skills/evals/SKILL.md`** — confirmed genuinely
   replaced, not merely deleted. New text: "Grading has two layers: v1
   artifact assertions (what a run produced) stay primary, and v2 adds
   opt-in trajectory assertions (how the run got there) via
   `EVAL_TRANSCRIPT` (specs/skill-evals/SPEC.md,
   specs/trajectory-evals/SPEC.md)." Both v1 and v2 named. PASS.

2. **~10-line failure-budget rule verbatim in `.claude/skills/evals/SKILL.md`**
   — line ~51-52 still reads: "Keep each `assert.sh` failure message under
   ~10 lines — that is the whole budget the grader returns to the
   orchestrator, never a transcript." Unchanged from base. PASS.

3. **codex mirror procedural equivalence** — `git diff <base> -- codex/.agents/skills/evals/SKILL.md`
   shows the same treatment: "v1 grades artifacts only: what a run produced,
   not the trajectory it took" replaced with "Grading has two layers: v1
   artifact assertions (what a run produced) stay primary, and v2 adds
   opt-in trajectory assertions (how the run got there) via
   `EVAL_TRANSCRIPT`", plus an added EVAL_TRANSCRIPT paragraph matching the
   .claude leg's content and worked-example shape (same
   `grep -q '"subagent_type":"scout"'` example, same opt-in/additive
   framing). The original "never a transcript" budget-rule sentence (at
   base line 41, "Keep each `assert.sh` failure message under ~10 lines:
   that is the whole budget the grader returns to the orchestrator, never a
   transcript.") is present unchanged in the current file — it shifted down
   to line ~54 only because the new paragraph was inserted above it; its
   own text is byte-identical to base. PASS.

4. **antigravity/plugin.json untouched** — `git diff <base> --stat -- antigravity/.agents/workflows/evals.md .claude-plugin/plugin.json`
   produced empty output (no changes). Confirmed via full-repo
   `git diff <base> --stat`, which lists exactly 4 changed files: the three
   Touch-listed files (`.claude/skills/evals/SKILL.md`,
   `.claude/skills/evals/reference.md`,
   `codex/.agents/skills/evals/SKILL.md`) plus the task file itself. No
   scope creep. PASS.

## Scope-creep check

`git diff <base> --stat` — 4 files changed, all either in the task's Touch
list or the task file itself. No unrelated edits.

## Additional note

The reference.md worked example cites
`evals/breakdown/02-scout-delegation/assert.sh` as "the live" example; this
file exists (committed by task 02, "docs: close out task 02
(scout-delegation trajectory scenario)"), so the cross-reference resolves
correctly.

## Overall verdict: PASS

All six acceptance commands pass verbatim. Task-specific correctness checks
(v1/v2 reframe genuinely present in both legs, budget rule verbatim and
untouched in both legs, procedural equivalence between .claude and codex
mirrors, no antigravity/plugin.json scope creep) all confirmed. The only
discrepancy is cosmetic: the task file's own Status line and checkboxes were
never updated to reflect completion (left at "in-progress" / all boxes
unchecked) even though the underlying work is complete and correct — this
does not affect the append-only check (no violation occurred) but is worth
flagging to the orchestrator so the task's bookkeeping gets updated.
