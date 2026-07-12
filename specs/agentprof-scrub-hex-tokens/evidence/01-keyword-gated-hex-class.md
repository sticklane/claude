# Verification evidence: 01-keyword-gated-hex-class

Verdict: PASS

## Criterion 1: go test + monkey grep

Command: `cd agentprof && go test ./internal/claude/ -run Scrub -v` then `grep -c 'monkey' agentprof/internal/claude/scrub_test.go`

Output tail:
```
--- PASS: TestScrubLeavesKeywordlessOrShortHexAlone (0.00s)
    --- PASS: TestScrubLeavesKeywordlessOrShortHexAlone/monkey_plus_40_hex (0.00s)
    --- PASS: TestScrubLeavesKeywordlessOrShortHexAlone/bare_sha_in_prose (0.00s)
    --- PASS: TestScrubLeavesKeywordlessOrShortHexAlone/keyword_outside_window (0.00s)
    --- PASS: TestScrubLeavesKeywordlessOrShortHexAlone/23_hex_with_keyword (0.00s)
=== RUN   TestScrubAppliesClassAThenClassB
--- PASS: TestScrubAppliesClassAThenClassB (0.00s)
=== RUN   TestCollectScrubsSecretsInTurnFrames
--- PASS: TestCollectScrubsSecretsInTurnFrames (0.00s)
PASS
ok  	github.com/sticklane/agentprof/internal/claude	0.212s
```
`grep -c 'monkey' ...` = 3. PASS.

## Criterion 2: grep keyword

Command: `grep -c 'keyword' agentprof/internal/claude/scrub_test.go`
Output: `7`. PASS (>=1).

## Criterion 3: additive-only diff

Command: `git diff main -- agentprof/internal/claude/scrub_test.go | grep -cE '^-[^-]'`
Output: `0` (grep exit 1, no matching lines = zero deletions). PASS.

## Criterion 4: check.sh green

Command: `bash agentprof/scripts/check.sh`
Output:
```
check: format-check ok
check: lint ok
check: tests ok
```
PASS.

## Behavioral intent (SPEC R2), read from scrub.go / scrub_test.go and exercised via `go test`

- (a) incident shape `Todoist token: <40-hex synthetic>` redacts — `TestScrubRedactsKeywordGatedHex/incident_shape`, PASS.
- (b) bare 40-hex SHA in prose, no keyword in window, untouched — `TestScrubLeavesKeywordlessOrShortHexAlone/bare_sha_in_prose`, PASS.
- (c) `monkey ` + 40-hex untouched (word-boundary keyword regex, `\bkey\b` does not match inside "monkey") — `.../monkey_plus_40_hex`, PASS.
- (d) 24-hex + keyword redacts, 23-hex + keyword untouched — `TestScrubRedactsKeywordGatedHex/24_hex_with_keyword` and `TestScrubLeavesKeywordlessOrShortHexAlone/23_hex_with_keyword`, both PASS, genuinely boundary-adjacent (24 vs 23 chars).
- (e) digit-free mixed-case hex + keyword redacts, isolating class (c) from class (b) (no digit ⇒ `hasDigitUpperLower` false ⇒ class (b) cannot match) — `.../digit-free_mixed_hex_with_keyword`, PASS.
- (f) (b)-before-(c) ordering: `"secret Ab1234567890cdef1234567890XY"` — the whole 28-char digit/upper/lower run (including non-hex `XY` tail) is consumed by class (b) first, leaving exactly one `[redacted]` — `.../whole_run_b_before_c`, PASS.

Independently verified `keyword_outside_window` is non-vacuous: hex run starts at byte 65, the preceding-40-byte window is bytes 25-65 (`"y long stretch of filler prose text zzz "`), which does not contain "token" (ends at byte 5) — genuinely outside the window.

All hex literals in the test table are synthetic (`deadbeef`, `cafef00d`, `abcdef0123456789...`, `aBcDeFaBcDeF...`) — no real-looking secret values.

## Scope check

`git diff main --name-only`:
```
agentprof/internal/claude/scrub.go
agentprof/internal/claude/scrub_test.go
specs/agentprof-scrub-hex-tokens/tasks/01-keyword-gated-hex-class.md
```
Only the two Touch-listed scrub files plus the task file itself changed. `denylist.go` and README untouched — matches the Touch list and the task's explicit "Do NOT touch" note.

## Append-only task-file check

Base: 44c213a. `git diff 44c213a -- specs/agentprof-scrub-hex-tokens/tasks/01-keyword-gated-hex-class.md` shows only a `<!-- PLAN ... -->` comment block inserted between the `Touch:` header and `## Goal`. No edits to Goal/Steps/Touch/Budget/acceptance-criterion text. Status was already `in-progress` at the base commit (set by commit 44c213a itself), so no additional Status change is present in this diff. Acceptance checkboxes remain unticked (`- [ ]`) in the current working file, consistent with allowed edits only.

## Overall

PASS on all four command-based acceptance criteria, PASS on independently-verified SPEC R2 behavioral intent, no scope creep, task file diff is append-only (PLAN block only).
