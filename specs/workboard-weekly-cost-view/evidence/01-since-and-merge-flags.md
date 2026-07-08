# Verification: 01-since-and-merge-flags

Verdict: PASS

## Append-only task-file check

Command: `git diff 939e914 -- specs/workboard-weekly-cost-view/tasks/01-since-and-merge-flags.md`

Result: PASS. Only change is an added PLAN comment block (lines 13-29, wrapped
in `<!-- PLAN (build): ... -->`), inserted between the header fields and
`## Goal`. Status line, Goal/Steps/Touch/Budget text, and all acceptance
criterion text are byte-identical to base. Acceptance checkboxes remain
unticked (worker did not tick them or update Status past `in-progress`) —
noted but not a violation of the append-only rule itself.

## Criterion 1: `cd agentprof && go test ./...` passes, including R1/R2 fixture tests

Command: `cd agentprof && go test ./...`
Output (tail):
```
ok  	github.com/sticklane/agentprof	(cached)
ok  	github.com/sticklane/agentprof/internal/bqtime	(cached)
ok  	github.com/sticklane/agentprof/internal/claude	(cached)
ok  	github.com/sticklane/agentprof/internal/fixturegen	(cached)
ok  	github.com/sticklane/agentprof/internal/gcp	(cached)
ok  	github.com/sticklane/agentprof/internal/merge	(cached)
ok  	github.com/sticklane/agentprof/internal/naming	(cached)
ok  	github.com/sticklane/agentprof/internal/otel	(cached)
ok  	github.com/sticklane/agentprof/internal/output	(cached)
ok  	github.com/sticklane/agentprof/internal/pprofenc	(cached)
ok  	github.com/sticklane/agentprof/internal/pricing	(cached)
ok  	github.com/sticklane/agentprof/internal/schema	(cached)
ok  	github.com/sticklane/agentprof/internal/vertex	(cached)
```
All packages pass, no failures.

Specific Step-1 fixture tests confirmed present and passing (via `go test -run` /
`grep -n "^func Test"`):
- `cmd_claude_test.go:69 TestClaudeSinceWithExplicitDaysIsUsageError` — since+days
  mutual exclusivity, nonzero exit, stderr mentions "since" and "days", no file
  written.
- `cmd_claude_test.go:88 TestClaudeSinceAloneWithDefaultDaysExitsZero` — since alone
  (days at default 30) is NOT an error, exit 0.
- `cmd_claude_test.go:105 TestClaudeMergeWithPbGzOutputIsUsageError` — merge +
  `.pb.gz` -o is a usage error, nonzero exit, no output file written.
- `cmd_claude_test.go:125 TestClaudeMergeEmptyFreshKeepsNonEvictedAndExitsZero` —
  empty-fresh merge exits 0, leaves 2 non-evicted cache samples untouched
  (verified via schema.Read on output).
- `cmd_claude_test.go:158 TestClaudeMergeAllEvictedWritesEmptyJSONLAndExitsZero` —
  all-evicted + empty-fresh merge exits 0, writes a 0-byte (valid empty) JSONL
  file, bypassing output.Write's zero-sample error.
- `internal/merge/merge_test.go:27 TestMergeDropsOverlappingSessionAndAppendsNewOnly`
  — overlap-drop (stale existing A dropped, fresh A of same session survives,
  count=1) + new-only append (session C appended) + non-overlapping existing (B)
  survives untouched.
- `internal/merge/merge_test.go:59 TestMergeEmptyFreshLeavesNonEvictedUntouched`
- `internal/merge/merge_test.go:78 TestMergeEvictsSamplesOlderThanSevenDays`
- `internal/merge/merge_test.go:98 TestMergeAllEvictedAndEmptyFreshYieldsEmpty`

All read the actual test bodies (not just names); assertions check parsed
structure (session counts, sample values, file size, schema.Read success) —
behavior-based, not implementation/string-matching.

Result: PASS

## Criterion 2: since + explicit --days → nonzero exit, stderr mentions both flags

Command: `cd agentprof && go run . claude --since 2020-01-01T00:00:00Z --days 1 -o /tmp/wwcv-vrfy`
Output:
```
agentprof claude: --since and --days are mutually exclusive
exit status 2
```
Shell `$?` after the `go run` wrapper = 1 (nonzero). The wrapper's own "exit
status 2" line confirms the underlying `run()` returned a nonzero (2) exit
code. stderr mentions both "--since" and "--days".

Result: PASS

## Criterion 3: since alone → exit 0

Command: `cd agentprof && go run . claude --since 2020-01-01T00:00:00Z -o /tmp/wwcv-vrfy`
Output: (no stderr/error text)
`$?` = 0

Result: PASS

## Criterion 4: gofmt -l . | wc -l → 0

Command: `cd agentprof && gofmt -l . | wc -l`
Output: `0`

Result: PASS

## Scope check

Command: `git diff --stat 939e914`
Output:
```
 agentprof/cmd_claude.go                            |  88 +++++++++++++
 agentprof/cmd_claude_test.go                       | 140 +++++++++++++++++++++
 agentprof/internal/merge/merge.go                  |  46 +++++++
 agentprof/internal/merge/merge_test.go             | 111 ++++++++++++++++
 .../tasks/01-since-and-merge-flags.md              |  18 +++
 5 files changed, 403 insertions(+)
```
- No changes to `agent-console/`.
- No changes to `agentprof/scripts/refresh-profile.sh`.
- No `--summary` flag added (grepped absent from cmd_claude.go changes; not
  referenced in diff).
- All touched files fall within the task's `Touch:` list
  (`agentprof/cmd_claude.go`, `agentprof/internal/`, `agentprof/testdata/` —
  no testdata files were actually touched, which is fine, Touch is a ceiling
  not a floor) plus the task file itself (plan-comment addition only, allowed).

Result: No scope creep found.

## Cleanup

`/tmp/wwcv-vrfy` and `/tmp/wwcv-x` removed after verification (confirmed via
`ls` returning "No such file or directory" for both).

## Overall verdict: PASS

All 4 acceptance criteria pass with exact command output matching
expectations. Task-file diff is append-only (plan comment block only).
No scope creep. Tests exercise real behavior (session counts, byte sizes,
schema round-trips), not literal-string overfitting.
