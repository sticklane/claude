# Verification: Task 06 — frame denylist scrub at sample-emit time

Verdict: PASS

## Acceptance criteria

1. `cd agentprof && go test ./internal/claude/`
   - Command: `cd agentprof && go test ./internal/claude/ -v`
   - Result: PASS — all tests including
     `TestScrubFramesRedactsSkillFrameAndDropsSubstring`,
     `TestScrubFramesRedactsProjectFrame`,
     `TestScrubFramesEmptyDenylistLeavesFramesUnchanged`,
     `TestLoadDenylistReadsLinesAndSkipsBlanks`,
     `TestLoadDenylistMissingFileIsNoDenylist`. `ok
     github.com/sticklane/agentprof/internal/claude 0.252s`.

2. `grep -qi 'denylist' agentprof/README.md`
   - Command: `grep -qi 'denylist' agentprof/README.md && echo GREP_PASS`
   - Result: GREP_PASS. README.md:187-215 has a "Frame denylist" section
     documenting the mechanism (path, format, `--frame-denylist` override,
     `(redacted)` marker, "never committed") AND a "Pinned-evidence repo
     rule" paragraph (line 210-215) requiring evidence profiles under
     specs/ to be generated with the denylist active. MANUAL criterion
     satisfied.

3. `bash agentprof/scripts/check.sh`
   - Result: green — `check: format-check ok`, `check: lint ok`,
     `check: tests ok`.

## Independent judgment on the Goal

- **Final frame-rewrite pass, not merely hooked into scrub.go.**
  `internal/claude/denylist.go` is a standalone file
  (`LoadDenylist`/`ScrubFrames`/`containsAny`) distinct from
  `internal/claude/scrub.go`'s secret scrub. `ScrubFrames` iterates every
  `schema.Sample.Stack` element and replaces any frame containing a
  denied substring with the literal `(redacted)` (distinct marker from
  scrub.go's `[redacted]`). Since all enumerated frame kinds (project,
  turn, skill, agent, role/stage, model) are `Stack` elements
  (confirmed via schema.go and denylist_test.go fixtures spanning
  project/skill frames), this pass covers all of them, including skill
  frames from `normalizeSkillFrame` which the task explicitly calls out
  as unscrubbed by scrub.go.
- **Wiring in cmd_claude.go**: `claude.ScrubFrames(samples, denied)` is
  called immediately after `Collect`/`CollectWithReprime` (line 80),
  before the merge/summary/direct-write branches, and again after
  `nameTurnFrames` (line 99) before the direct `output.Write` call —
  matching the plan's stated rationale (renaming rewrites turn frames
  after the first scrub pass).
- **Denylisted substring nowhere in emitted JSONL**: verified via
  `TestScrubFramesRedactsSkillFrameAndDropsSubstring`, which marshals the
  scrubbed sample through `schema.MarshalLine` (the real wire format) and
  asserts `strings.Contains(out, "zz-test")` is false.
- **No denylist file → unchanged output**: `TestScrubFramesEmptyDenylistLeavesFramesUnchanged`
  compares before/after marshaled JSONL with `ScrubFrames(samples, nil)`
  and asserts byte-identical output; `TestLoadDenylistMissingFileIsNoDenylist`
  confirms `LoadDenylist` returns `nil, nil` for a missing path (no error),
  which is what `defaultFrameDenylist()`'s default path relies on when
  unconfigured.
- **Fixture uses invented name**: denylist_test.go uses `skill:zz-test-private`
  / `zz-test-private-proj` throughout — `grep -rl "zz-test" .` in
  agentprof/ finds only `internal/claude/denylist_test.go`; no denylist
  file is committed anywhere in the repo (`find . -iname '*denylist*'`
  finds only the two .go source files).

## Task-file append-only check

`git diff 4931e41 -- specs/agentprost-attribution-gaps/tasks/06-frame-denylist.md`
(actual path: specs/agentprof-attribution-gaps/tasks/06-frame-denylist.md)
shows a single hunk: insertion of the `<!-- PLAN (worker, ...) -->` comment
block (22 lines added) between the Touch header and `## Goal`. Nothing else
changed — Status line still reads `in-progress`, acceptance checkboxes are
still unticked (`- [ ]`), and Goal/Steps/Touch/Budget/acceptance criterion
text is byte-identical to base 4931e41. This is compliant with the
append-only contract (plan comment block is an allowed addition), but note:
the worker did not flip Status or tick the acceptance boxes/add
evidence-citation lines despite implementing and passing all three
criteria — a bookkeeping gap, not a correctness problem. Flagging as a
finding for the orchestrator to update post-verification.

## Scope / Touch check

`git diff 4931e41 --stat` (excluding the task file) touches only:
- `agentprof/README.md` (+30)
- `agentprof/cmd_claude.go` (+22)
- `agentprof/internal/claude/denylist.go` (new, +71)
- `agentprof/internal/claude/denylist_test.go` (new, +109)

All within Touch: `agentprof/internal/claude/, agentprof/cmd_claude.go,
agentprof/testdata/, agentprof/README.md`. No `agentprof/testdata/` files
were added (not required by Touch, just permitted). `internal/output/` is
untouched — confirmed not present in the diff stat. No out-of-scope edits
found.

## Overfitting check

Test fixtures use a substring (`zz-test`) of a fixture-only invented skill
name, not special-cased exact-match logic — `ScrubFrames`/`containsAny`
use generic `strings.Contains`, which is substring matching for arbitrary
denylist entries, not a hardcoded check against the test's literal
strings. The implementation would work correctly for any other denylist
string/frame combination; it is not overfit to the test inputs.

## Commands run (raw, for reference)

```
cd agentprof && go test ./internal/claude/ -v   # PASS, ok ... 0.252s
grep -qi 'denylist' agentprof/README.md && echo GREP_PASS   # GREP_PASS
bash agentprof/scripts/check.sh   # check: format-check ok / lint ok / tests ok
git diff 4931e41 --stat
git diff 4931e41 -- specs/agentprof-attribution-gaps/tasks/06-frame-denylist.md
grep -rl "zz-test" .   # only denylist_test.go
find . -iname '*denylist*'   # only the two .go source files
```
