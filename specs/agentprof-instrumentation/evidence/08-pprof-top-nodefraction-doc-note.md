# Verification: Task 08 — pprof -top node-fraction doc note

Verdict: PASS

## Criteria

1. `cd agentprof && grep -qi 'nodefraction' README.md`
   Exit code: 0
   Evidence: match found at README.md:64-65 ("node-fraction pruning ... -nodefraction=0").

2. `cd agentprof && grep -i 'nodefraction' README.md | grep -q 'tool:'`
   Exit code: 0
   Evidence: same note line ties pruning to `tool:` frames: "hides small `tool:` frames unless you pass `-nodefraction=0 -edgefraction=0`".

3. `cd agentprof && bash scripts/check.sh`
   Exit code: 0
   Output:
   ```
   check: format-check ok
   check: lint ok
   check: tests ok
   ```

## Additional confirmations

(a) Placement adjacent to plain `-top` invocation: confirmed. README.md lines 58-68:

```
go tool pprof -top week.pb.gz
```

```
The default metric is `cost_microusd` (1,000,000 = $1).

> **Note:** `-top`'s default node-fraction pruning
> hides small `tool:` frames unless you pass `-nodefraction=0 -edgefraction=0`
> (or narrow the window with `--days` or a `--focus` project filter) — so a
> missing `tool:` frame on a day-scale profile reads as pruning, not a broken
> feature.
```

The note sits immediately after the `go tool pprof -top week.pb.gz` example, before the "Switching metrics" section — directly adjacent as required.

(b) Content ties node-fraction pruning to `tool:` frames and mentions both flags: confirmed — "node-fraction pruning hides small `tool:` frames unless you pass `-nodefraction=0 -edgefraction=0`".

(c) Diff scope: `git diff 16a3bbc8936ac7a55c90f6865210864f212e5f3d --numstat` →

```
6	0	agentprof/README.md
```

Only agentprof/README.md touched (matches Touch: agentprof/README.md). Full diff shows a clean 6-line insertion (blockquote note + trailing blank line) with no reflow/reformatting of surrounding text:

```diff
+> **Note:** `-top`'s default node-fraction pruning
+> hides small `tool:` frames unless you pass `-nodefraction=0 -edgefraction=0`
+> (or narrow the window with `--days` or a `--focus` project filter) — so a
+> missing `tool:` frame on a day-scale profile reads as pruning, not a broken
+> feature.
+
```

## Task-file append-only check

`git diff 16a3bbc8936ac7a55c90f6865210864f212e5f3d -- specs/agentprof-instrumentation/tasks/08-pprof-top-nodefraction-doc-note.md` produced no output — the task file is byte-identical to the base commit (Status still reads `in-progress`, no boxes ticked, no evidence lines added yet). This is pre-close-out per the caller's note and is not a violation; trivially append-only (zero diff).

No other task files under specs/agentprof-instrumentation/tasks/ were touched (`--numstat` on the tasks/ dir returned empty).

## Scope creep

None found. Diff is confined to the single required README.md paragraph.

## Gate

`bash scripts/check.sh` (format-check, lint, tests) — all green, exit 0.
