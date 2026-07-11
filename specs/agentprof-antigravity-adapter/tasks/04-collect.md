# Task 04: `internal/antigravity.Collect` — join, Stack/Labels, token mapping

Status: pending
Depends on: 01, 02, 03
Priority: P1
Budget: 24 turns
Spec: ../SPEC.md (Solution item 2; R1; R2)
Touch: agentprof/internal/antigravity/antigravity.go, agentprof/internal/antigravity/antigravity_test.go, agentprof/internal/antigravity/testdata/conversations-corrupt/ (the corrupted-copy fixture for the skip-on-lock/corrupt test — do NOT add or modify anything under testdata/conversations/, which holds Task 01's real fixture untouched), agentprof/go.mod, agentprof/go.sum

## Goal

`internal/antigravity.Collect(dir string, cutoff time.Time) ([]schema.Sample,
int, error)` globs `<dir>/conversations/*.db`, opens each SQLite file
read-only, joins `steps` (`step_type=15`) to `gen_metadata` on `idx`, and
emits one `schema.Sample` per joined row within the cutoff window — with
`Time`, `Stack`, `Labels`, and (once R0's fixture confirms the mapping)
token-count `Values`, plus a skipped-row count for locked/corrupt files or
unparseable blobs. This is the core adapter logic; R1 (structure/join/
Stack/Labels) and R2 (token mapping) land together because SPEC.md tests
them in the same integration suite against the same committed fixture.

## Touch

Only `antigravity.go`/its test, plus adding a SQLite driver dependency to
go.mod/go.sum, plus one additional corrupted-copy fixture file under the
sibling `testdata/conversations-corrupt/` directory for the skip-path
test. Do NOT add or modify anything under the real fixture's
`testdata/conversations/` directory Task 01 committed to — copy the real
`.db` out to `conversations-corrupt/` and corrupt that copy (e.g.
truncate/flip bytes), leaving `conversations/`'s contents byte-for-byte
untouched (this also keeps `Collect`'s `<dir>/conversations/*.db` glob
from ever picking up the corrupted copy when pointed at the main fixture
dir). Do not touch `internal/antigravity/protowire.go` (Task 02, already
done) or `internal/pricing/` (Task 03, already done) — only call into
them.

## Steps

1. Add a pure-Go SQLite driver (e.g. `modernc.org/sqlite`, no cgo — keeps
   `go build` portable across worker machines) to `go.mod`; run
   `go mod tidy` after adding the import.
2. Write the failing tests first in `antigravity_test.go`, all driven off
   the COMMITTED fixture from Task 01 (`internal/antigravity/testdata/
   conversations/<cascade_id>.db`) — never a live `~/.gemini` path:
   a. `Collect` on the fixture dir returns at least one `schema.Sample`,
      with `Time` matching the fixture row's field-9.4 Timestamp.
   b. The Stack's project frame matches the expected basename/label from
      the field-1/field-18 extraction rule (Solution item 2): prefer field
      18's project label when present and non-empty, fall back to the
      workspace-URI (field 1, sub-field 1) basename otherwise.
   c. `Values` includes `input_tokens`/`output_tokens`/`cache_read_tokens`
      per the sub-field mapping Task 01's README justifies (any sub-field
      the README can't confirm stays OUT of `Values` — do not guess), plus
      `calls: 1` and `cost_microusd` (calling `pricing.PriceGemini` with
      the raw, unmodified field-21 display string from Task 03).
   d. `Labels` includes `source: "antigravity"`, `session` = the cascade_id
      (confirm it equals the `.db`'s own basename), `trajectory_id`,
      `model_raw` (the raw field-21 string, unmodified — must be
      byte-identical to what's passed to `PriceGemini`), and `db_file`.
   e. A corrupted copy of the fixture (see Steps 3) is opened, fails to
      parse, and is counted in the skipped-row return rather than erroring
      the whole `Collect` call.
   f. `Collect` on an empty/nonexistent directory returns zero samples,
      zero skipped, no error (not an exit code — that's Task 05/R6).
3. Create the corrupted-copy fixture: copy the real `.db`, truncate or
   flip bytes in one `gen_metadata` blob, save as e.g.
   `internal/antigravity/testdata/conversations-corrupt/<id>-corrupt.db`
   (a location `Collect`'s glob for the main fixture dir won't pick up —
   point the skip-path test at this path explicitly, not at the main
   `testdata/conversations/` dir alongside the real fixture).
4. Confirm the tests fail (no implementation yet).
5. Implement `Collect`: glob, open read-only (`file:...?mode=ro`), retry
   once on a locked db (active `-wal`/`-shm` pair) before skipping with a
   stderr note, join `steps`/`gen_metadata` on `idx` for `step_type=15`
   rows, decode blobs via Task 02's `protowire` package, and build each
   `schema.Sample` per Solution item 2's exact field paths.
6. Get tests green. Leave any token sub-field the fixture's README can't
   confidently justify OUT of `Values` (Solution's explicit rule) rather
   than guessing.

## Acceptance

- [ ] `cd agentprof && go test ./internal/antigravity/... -v` → passes: walker tests (Task 02, unaffected), plus all of this task's `Collect`-level tests (join, skip-on-lock/corrupt, Stack project frame, token mapping, empty-dir zero-samples) against the COMMITTED fixture
- [ ] `cd agentprof && go build ./...` → succeeds with the new SQLite dependency
- [ ] `cd agentprof && go vet ./internal/antigravity/...` → clean
