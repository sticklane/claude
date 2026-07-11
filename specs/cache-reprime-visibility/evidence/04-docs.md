# Verification: cache-reprime-visibility / 04-docs

Verdict: PASS

## Criteria

1. ✓ `grep -qi 'reprime' agentprof/SCHEMA.md && grep -qi 'reprime' agentprof/README.md`
   Output: `SCHEMA HIT` / `README HIT` — both files mention reprime.

2. ✓ `grep -qi 'tagfocus reprime' agentprof/README.md`
   Output: `TAGFOCUS HIT`. README shows:
   ```
   go tool pprof -tagfocus reprime=true week.pb.gz
   ```

3. ✓ `bash agentprof/scripts/check.sh`
   Output:
   ```
   check: format-check ok
   check: lint ok
   check: tests ok
   ```

## Accuracy check against shipped code (docs must follow code)

- `agentprof/internal/claude/claude.go`: `DefaultReprimeThreshold = 50000`;
  `CollectWithReprime` marks `reprime=true` only when `reprimeThreshold > 0
  && i > 0 && r.usage.CacheCreationTokens > threshold` on **main-loop**
  samples (the loop building `mainP.responses`); subagent loop below never
  sets the label. SCHEMA.md's "The `reprime` label" section states exactly
  this: main-loop, non-first call, `cache_write_tokens` > `--reprime-threshold`
  (default 50000), subagents and the first call never marked. README repeats
  the same rule alongside the worked `-tagfocus reprime=true` example. Match
  confirmed.

- `agentprof/internal/costsummary/costsummary.go`:
  - `Reprime` struct: `Count→count`, `CacheWriteTokens→cache_write_tokens`,
    `CostMicrousd→cost_microusd`, `ByProject→by_project`. SCHEMA.md's
    "Cost-summary sections" bullet for `reprime` names exactly these four
    fields. Match confirmed.
  - `SessionStat` struct: `Project→project`, `Calls→calls`,
    `CostMicrousd→cost_microusd`, `P50Ctx→p50_ctx`, `P90Ctx→p90_ctx`.
    SCHEMA.md's `sessions` bullet names `project`, `calls`, `cost_microusd`,
    `p50_ctx`/`p90_ctx`. Match confirmed.
  - `sessionStats()` explicitly excludes samples with an `agent:` frame
    (`if _, hasAgent := agentType(smp.Stack); hasAgent { continue }`) —
    main-loop-only. SCHEMA.md states percentiles are "computed over that
    session's main-loop model calls only — subagent calls carry the parent's
    session label but are excluded." Match confirmed.
  - Context definition `cache_read_tokens + input_tokens` — SCHEMA.md states
    the same. Match confirmed.

No discrepancies found between the new prose and the shipped Go code.

## Scope / diff check

`git diff --stat ce0793d3f0e5665c6ea7469fc402a1023b8a09e9 -- .` (run from
worktree root):
```
 agentprof/README.md | 13 +++++++++++++
 agentprof/SCHEMA.md | 44 +++++++++++++++++++++++++++++++++++++++++++-
 2 files changed, 56 insertions(+), 1 deletion(-)
```
Docs-only, matches the task's `Touch: agentprof/SCHEMA.md, agentprof/README.md`.
No Go code changed — consistent with "no code changed" acceptance clause.

## Task-file append-only check

`git diff ce0793d3f0e5665c6ea7469fc402a1023b8a09e9 -- '*/tasks/*.md'` →
empty (no output). The task file `specs/cache-reprime-visibility/tasks/
04-docs.md` was not modified at all in this worktree: `Status:` line still
reads `in-progress`, and no acceptance checkboxes were ticked. This is not
an append-only *violation* (nothing illegal was added), but the task's
bookkeeping was left incomplete — worth flagging as a process gap, not a
criterion failure, since the task's actual acceptance criteria are the
three runnable commands above and all three pass.

## Findings

- No scope creep: diff touches only the two docs files named in Touch.
- No overfitting: docs are prose, not test-gamed logic; nothing to game.
- Minor process gap: task file Status/checkboxes not updated to reflect
  completion (does not affect PASS verdict on the stated acceptance
  criteria).
