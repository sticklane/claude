# Task 01: Keyword-gated hex class in scrub

Status: done
Depends on: none
Priority: P1
Budget: 8 turns
Spec: ../SPEC.md (requirements R1, R2)
Touch: agentprof/internal/claude/scrub.go, agentprof/internal/claude/scrub_test.go

## Goal

`scrub()` gains class (c): a maximal `[0-9a-fA-F]{24,}` run is replaced
with `[redacted]` iff the word-boundary keyword regex
`(?i)\b(token|key|secret|password|bearer|credential|api[-_]?key)\b`
matches within the 40 bytes immediately preceding the run's first byte.
Class (c) runs strictly after (a) and (b); already-redacted spans are not
double-processed. The full behavior table from ../SPEC.md R2 is pinned in
`scrub_test.go`.

## Touch

The two scrub files only. Do NOT touch `denylist.go` (separate shipped
mechanism), any other `internal/claude` file, or README (task 02).

## Steps

1. RED: add the R2 table-driven cases first and watch them fail —
   including the incident shape verbatim (`Todoist token: ` + a SYNTHETIC
   40-char lowercase-hex value, never the real one), `monkey ` + 40-hex
   untouched, bare 40-hex SHA in prose untouched, keyword outside the
   40-byte window untouched, 24-hex redacted / 23-hex untouched,
   digit-free mixed-case hex (isolates (c) from (b)) redacted, and the
   whole-run (b)-before-(c) ordering case. Existing test expectations are
   not edited.
2. GREEN: implement class (c) after the existing two passes.
3. REFACTOR with tests green; update scrub.go's header comment to
   describe the three classes.

## Acceptance

- [x] `cd agentprof && go test ./internal/claude/ -run Scrub` → pass, with the full R2 table present (`grep -c 'monkey' agentprof/internal/claude/scrub_test.go` → ≥ 1) — verifier: tests ok, monkey count = 3 (evidence/01-keyword-gated-hex-class.md)
- [x] `grep -c 'keyword' agentprof/internal/claude/scrub_test.go` → ≥ 1 — verifier: count = 7 (evidence/01-keyword-gated-hex-class.md)
- [x] `git diff main -- agentprof/internal/claude/scrub_test.go` shows no deleted assertions on pre-existing cases (additive table only) — verifier: 0 deletion lines, 44 additions (evidence/01-keyword-gated-hex-class.md)
- [x] `bash agentprof/scripts/check.sh` → green — verifier: format-check ok, lint ok, tests ok (evidence/01-keyword-gated-hex-class.md)
