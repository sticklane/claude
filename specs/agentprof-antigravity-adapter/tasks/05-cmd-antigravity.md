# Task 05: `cmd_antigravity.go` subcommand + main.go wiring

Status: in-progress
Depends on: 04
Priority: P1
Budget: 10 turns
Spec: ../SPEC.md (Solution item 4; R5; R6)
Touch: agentprof/cmd_antigravity.go, agentprof/cmd_antigravity_test.go, agentprof/main.go

## Goal

`agentprof antigravity` is a working subcommand:
`cmdAntigravity(args []string, stdout, stderr io.Writer) int`, mirroring
`cmdClaude`'s flag shape for `--antigravity-dir` (default
`~/.gemini/antigravity-cli`), `--days`/`--since`, and `-o` (reusing
`internal/output` unchanged). It exits 1 with a "no samples found" stderr
message when `Collect` returns zero samples, matching `cmd_claude.go`'s
existing empty-result guard. `-o summary` reuses `summary.go`'s existing
`summarize()`/`summaryRow` shape unchanged — the same JSON array shape
`agentprof claude -o summary` already emits. `--merge` and `--summary
<path>` are explicitly OUT OF SCOPE (Solution item 4) — do not wire them.

## Touch

New `cmd_antigravity.go` + its test, plus the one-line addition to
`main.go`'s subcommand switch. Do not touch `cmd_claude.go`,
`internal/costsummary`, or `summary.go` — reuse them unchanged.

## Steps

1. Write the failing test first in `cmd_antigravity_test.go`, mirroring
   `cmd_claude_test.go`'s empty-result test: `cmdAntigravity` given an
   empty/nonexistent `--antigravity-dir` exits 1 and writes a "no samples
   found" message to stderr.
2. Add a second test: `cmdAntigravity` against the committed fixture at
   `internal/antigravity/testdata` with `-o summary --days 3650` exits 0
   and writes a JSON array to stdout matching `summaryRow`'s shape
   (`session`, `model`, `input_tokens`, `output_tokens`,
   `cache_read_tokens`, `cache_write_tokens`, `cost_microusd`, `priced`).
3. Confirm both tests fail (no `cmd_antigravity.go` yet).
4. Implement `cmd_antigravity.go`: parse `--antigravity-dir`
   (default `~/.gemini/antigravity-cli`), `--days`/`--since`, `-o`; call
   `antigravity.Collect`; on zero samples, print the "no samples found"
   message to stderr and return 1 (this exit-code guard lives here, in
   package `main`, not in `internal/antigravity`); for `-o summary`, feed
   the samples through `summary.go`'s existing `summarize()` and print the
   `summaryRow` JSON array via `internal/output` unchanged.
5. Wire `case "antigravity": return cmdAntigravity(args[1:], stdout,
   stderr)` into `main.go`'s subcommand switch, alongside `claude`/`gcp`/
   `vertex`/`otel`.
6. Get tests green.

## Acceptance

- [ ] `cd agentprof && go test ./... -run TestCmdAntigravity -v` → both new tests pass
- [ ] `cd agentprof && go build ./...` → succeeds with `cmd_antigravity.go` wired into `main.go`
- [ ] `cd agentprof && go build -o agentprof . && ./agentprof antigravity -o summary --antigravity-dir internal/antigravity/testdata --days 3650` → exits 0, prints a JSON array matching `summaryRow`'s shape (same shape as `agentprof claude -o summary`)
- [ ] `cd agentprof && ./agentprof antigravity -o summary --antigravity-dir /tmp/does-not-exist --days 3650; echo "exit=$?"` → exit 1, stderr contains "no samples found"
