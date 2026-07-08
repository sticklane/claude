# Task 01: agentprof claude --since and --merge (incremental JSONL cache)

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers, in every task file — and ## Progress / ## Deferred questions are drain-written sections (single writer, main checkout): workers report that content, never write it. -->

Status: in-progress
Depends on: none
Priority: P1
Budget: 20 turns
Spec: ../SPEC.md (requirements R1, R2)
Touch: agentprof/cmd_claude.go, agentprof/internal/, agentprof/testdata/

## Goal

`agentprof claude` accepts `--since <RFC3339>` (absolute cutoff through the
same `inWindow()` max-mtime check as `--days`; combining with an
EXPLICITLY-passed `--days`, detected via `flag.FlagSet.Visit`, is a usage
error) and `--merge <path>` (JSONL rolling cache: read existing via
`schema.Read` with missing-file = zero samples; drop existing samples whose
session label appears among fresh samples; append fresh; evict samples
older than `now - 7d`; write to `-o`). In `--merge` mode both zero-sample
guards are bypassed per SPEC.md — an empty merged result writes a valid
empty JSONL file, and `--merge` with a `.pb.gz` `-o` is a usage error
(pprof can't round-trip per-sample Time).

## Touch

Go only. Do NOT touch `agent-console/` (task 03) or
`agentprof/scripts/refresh-profile.sh` (task 04). The summary flag (R3) is
task 02 — leave `--summary` out entirely.

## Steps

1. Write the failing tests first: `--since`+explicit-`--days` mutual
   exclusivity via `fs.Visit` (including that `--since` alone, with
   `--days` at its default 30, is NOT an error); merge fixture with one
   overlapping session (old samples dropped, not duplicated) and one
   new-only session (appended); empty-fresh merge run exits 0 and leaves
   non-evicted samples untouched; all-evicted + empty-fresh run writes a
   valid EMPTY JSONL file and exits 0 without routing through
   `output.Write`'s zero-sample error; `--merge` + `.pb.gz` `-o` → usage
   error, no output written.
2. Implement `--since` against `inWindow()` (see
   `internal/claude/claude.go:108-147,185-201`, refs approximate).
3. Implement `--merge` using ONLY the existing `schema.Read`/`output.Write`
   round-trip — no new encoder/decoder.
4. Bypass `cmdClaude`'s pre-write "no samples found" check whenever
   `--merge` is set, and write empty results directly (truncate) instead
   of calling `output.Write` with an empty slice.

## Acceptance

- [ ] `cd agentprof && go test ./...` → pass, including all R1/R2 fixture
      tests listed in Steps 1.
- [ ] `cd agentprof && go run . claude --since 2020-01-01T00:00:00Z --days 1 -o /tmp/wwcv-x` →
      nonzero exit, stderr mentions both flags (R1).
- [ ] `cd agentprof && go run . claude --since 2020-01-01T00:00:00Z -o /tmp/wwcv-x` →
      exit 0 (R1).
- [ ] `cd agentprof && gofmt -l . | wc -l` → 0.
