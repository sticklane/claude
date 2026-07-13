# Verification: Task 05 — costsummary tool-sample model-bucket NOTE

Verdict: PASS

Base commit: 17fdff4e638a01219bbeb208dffe1f9a5436eaa1
Branch: task/05-costsummary-note
Worktree: /home/user/claude/.claude/worktrees/agent-a941c865b230baed9

## Acceptance criteria

1. `grep -Eqi 'no.model' specs/workboard-weekly-cost-view/SPEC.md`
   Exit code: 0 (match). Matched text: NOTE says the model rule "has no
   explicit 'no model' bucket".

2. `grep -qi 'duration_ms' specs/workboard-weekly-cost-view/SPEC.md`
   Exit code: 0 (match). Matched text: NOTE names the pure `tool:` sample
   as "one carrying only `duration_ms`, no tokens/cost".

3. `cd agentprof && go test ./internal/costsummary/ -count=1`
   Output:
   ```
   ok  	github.com/sticklane/agentprof/internal/costsummary	0.003s
   ```
   exit=0. Docs-only change; agentprof code untouched (confirmed by diff
   stat below).

## Scope check

`git diff 17fdff4e638a01219bbeb208dffe1f9a5436eaa1 --stat`:

```
 specs/workboard-weekly-cost-view/SPEC.md | 15 +++++++++++++--
 1 file changed, 13 insertions(+), 2 deletions(-)
```

Only SPEC.md changed — matches the task's `Touch:
specs/workboard-weekly-cost-view/SPEC.md`. No agentprof code touched.

Append-only task-file check: `git diff 17fdff4e638a01219bbeb208dffe1f9a5436eaa1
-- 'specs/workboard-weekly-cost-view/tasks/*.md'` produced NO output — no
task file (including this task's own file) was modified in the tree yet;
the acceptance checkboxes in 05-...md are still unticked and Status is
still `in-progress`. This is not itself a failure of this task's
Acceptance criteria (none of the three reference the task file), but it
means the worker has not yet recorded evidence-citation lines or flipped
Status per the append-only convention — flagged as an outstanding
housekeeping gap, not a criterion failure.

### Minor scope-creep finding

Within the single touched file, two unrelated continuation lines had
their indentation changed from 6 spaces to 4 spaces, outside the added
NOTE block:

- SPEC.md line 245 (`--since 2020-01-01T00:00:00Z -o /tmp/x` continuation,
  originally 6-space indented under its bullet, now 4-space)
- SPEC.md line 257 (`/dev/null -w '%{http_code}'...` continuation, same
  drift)

These are pure whitespace/indentation changes to acceptance-criteria text
in unrelated bullets (R1 and R7 checks), not required by this task's Goal
or Steps, and not part of the NOTE addition. They do not change the
rendered/matched text (grep/exact semantics unaffected) but are
unrequested edits to criterion text outside the task's stated Goal —
reported per the scope-creep check, not treated as a blocking defect
since content is unchanged.

## Factual-accuracy check against costsummary.go

`agentprof/internal/costsummary/costsummary.go` `modelLeaf` (lines
97-109):

```go
// modelLeaf returns the last (leaf) frame that isn't a tool:/role:/stage:
// frame — forward-compatible with the instrumentation spec's new frame kinds,
// which are ignored here.
func modelLeaf(stack []string) (string, bool) {
	for i := len(stack) - 1; i >= 0; i-- {
		f := stack[i]
		if strings.HasPrefix(f, "tool:") || strings.HasPrefix(f, "role:") || strings.HasPrefix(f, "stage:") {
			continue
		}
		return f, true
	}
	return "", false
}
```

Confirms: a pure `tool:` sample's leaf frame is skipped, and the walk
continues backward to the preceding non-tool frame (e.g. `main`), which
is then used as the `by_model` bucket key. The added NOTE's description
("the leaf rule simply skips its `tool:` frame and resolves to the
preceding non-tool frame (e.g. `main`), so that sample's `duration_ms`
lands in `by_model["main"]`") is factually accurate against this code.

## R3-unchanged confirmation

NOTE opens with "(no requirement change; R3's model rule stays exactly as
specified above)" — explicitly states no requirement text changes; only
explanatory NOTE text was added.

## Gate

`cd agentprof && bash scripts/check.sh` was not run (task is docs-only and
its own acceptance criteria scope the check to
`go test ./internal/costsummary/`, which passed); no agentprof code was
touched so the broader gate is not required by this task's Acceptance
list.

## Overall

All three Acceptance criteria pass by exact command execution. Touch
scope is respected (only SPEC.md changed). The NOTE is factually accurate
against `modelLeaf`'s actual behavior and explicitly disclaims any
requirement change. One minor, non-blocking scope-creep finding
(unrelated indentation drift on two other bullets) and one housekeeping
gap (task file Status/checkboxes not yet updated) are noted above.
