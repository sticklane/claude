# Task 04: `internal/antigravity.Collect` — join, Stack/Labels, token mapping

Status: done
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

- [x] `cd agentprof && go test ./internal/antigravity/... -v` → passes: walker tests (Task 02, unaffected), plus all of this task's `Collect`-level tests (join, skip-on-lock/corrupt, Stack project frame, token mapping, empty-dir zero-samples) against the COMMITTED fixture
- [x] `cd agentprof && go build ./...` → succeeds with the new SQLite dependency
- [x] `cd agentprof && go vet ./internal/antigravity/...` → clean

## Evidence

Confirmed via `protoc --decode_raw` against the committed fixture
`d147c9da-…​.db`; all values now asserted in `antigravity_test.go`.

Two SPEC field-path assumptions were DISPROVEN by the real fixture and
corrected in the implementation (downstream tasks 05/06 and a SPEC touch-up
should note these):

1. **Join key is positional, not `idx`-equality.** The lone `step_type=15`
   step is `steps.idx=2`, but its `gen_metadata` row is `idx=0`.
   `gen_metadata.idx` is a 0-based generation ordinal, not the step index.
   `Collect` joins the k-th `step_type=15` step (ordered by `steps.idx`) to
   `gen_metadata.idx=k` via a `ROW_NUMBER()` window join — SPEC Solution
   item 2's "join … on idx" (equality) would return zero rows here.
2. **The gen fields the SPEC numbers live under top-level wrapper field 1.**
   The `gen_metadata.data` blob wraps the generation submessage in top-level
   field 1; the token submessage (4), Timestamp (9.4), display string (21),
   and `{key,value}` map (20) are all at `1→N`, not at the blob root. (Top-
   level field 3 is a separate config/tool-definitions block that also
   carries a same-numbered field 4/21 with different meaning — reading at the
   blob root would silently grab the wrong bytes.)

Confirmed mappings (from gen wrapper `1→…`): `Time` = `9→4` Timestamp
(1783813771 s / 429751000 ns → 2026-07-11T23:49:31.429751Z); `input_tokens`
= `4` sub-field 2 (17234); `output_tokens` = `4` sub-field 3 (71);
`cost_microusd` = 5348 (`PriceGemini("Gemini 3.5 Flash (Medium)")`).
`cache_read_tokens` is deliberately OMITTED: the README's sub-fields 6/9/10
are unidentified, so per Solution's no-guess rule no cache metric is emitted.
`session` = cascade_id = `.db` basename (`d147c9da-…`); `trajectory_id`
(`2d277f57-…`) comes from the `20` map and matches `trajectory_meta`. Project
frame resolves to `trajectory_metadata_blob` field 18 (`eda80a54-…`, a
per-project UUID here because the fixture used `--new-project`); the
workspace-URI-basename fallback is covered by a separate hand-built-blob unit
test.

The corrupted-copy fixture lives at
`internal/antigravity/testdata/conversations-corrupt/…-corrupt.db` (journal
mode DELETE, its one `gen_metadata` blob overwritten with an unparseable
byte sequence) — the real `testdata/conversations/` fixture is byte-for-byte
untouched. Tests stage a byte-copy of the real (WAL-mode) fixture into a temp
dir before reading, so SQLite's read-only WAL sidecars never dirty the
tracked `testdata/` directory.
