# Task 02: Hand-rolled protobuf field-walker

Status: in-progress
Depends on: none
Priority: P0
Budget: 16 turns
Spec: ../SPEC.md (Solution item 1; R1's walker-isolation coverage)
Touch: agentprof/internal/antigravity/protowire.go, agentprof/internal/antigravity/protowire_test.go

## Goal

A minimal, hand-rolled protobuf wire-format field-walker exists at
`agentprof/internal/antigravity/protowire.go` — a tag/varint/length-delimited
reader that extracts specific `(field number, wire type)` paths from raw
protobuf bytes with no dependency on `protoc` or a generated `.pb.go`. It
reads only the field numbers this adapter needs and treats everything else
as opaque/skippable (the wire format's own self-describing design).
Malformed or unrecognized bytes in a blob cause a per-call skip/error
return, never a panic. This is the riskiest new code in the adapter
(Solution item 1) and is unit-tested in complete isolation from `Collect` —
Task 04 will call into this package but must not need to touch it.

## Touch

Only `protowire.go` and its test file. Do not touch `antigravity.go`,
`Collect`, or any SQLite/db-opening code — that is Task 04's job and
depends on this package's exported API, not the reverse. Building this
task's test fixtures as hand-crafted byte slices (not a real `.db` file)
keeps it independent of Task 01's fixture.

## Steps

1. Write the failing tests first in `protowire_test.go`, using hand-crafted
   byte slices (construct varints and length-delimited fields by hand, or
   with a small test helper) — no real `.db` file needed:
   - Decoding a single varint field.
   - Decoding a length-delimited (string/bytes) field.
   - Extracting a nested field path (e.g. an outer submessage's field 4,
     then that submessage's field 9, sub-field 4 — mirroring the spec's
     `9.4` Timestamp path) — confirm the walker can descend into a
     length-delimited submessage and read a field inside it.
   - A repeated `{key, value}` string-map field (mirroring `gen_metadata`
     field 20) yielding multiple key/value pairs.
   - A malformed/truncated input (e.g. a varint that never terminates, or
     a length-delimited field whose declared length exceeds the remaining
     bytes) returns an error/skip rather than panicking or looping forever.
   - An unknown field number/wire type is skipped without affecting
     extraction of the fields that follow it.
2. Run the tests, confirm they fail (no implementation yet).
3. Implement `protowire.go`: a reader over `[]byte` exposing enough surface
   for Task 04 to pull specific field paths out of `gen_metadata`,
   `steps.metadata`, and `trajectory_metadata_blob` blobs — e.g. a
   `func ReadField(data []byte, fieldNum int) (wireType int, value []byte, ok bool)`
   plus varint helpers, shaped however is simplest for a targeted extractor
   (exact function names are this task's implementation choice — Task 04
   only needs a documented, exported way to walk a field path and get bytes
   back for a given field number).
4. Get tests green. Do not add a general-purpose decoder, field-name
   registry, or `.proto`-driven codegen — Out of scope explicitly excludes
   this; keep it to exactly the field paths this spec's parsing needs.
5. Add a short doc comment at the top of `protowire.go` noting it is a
   targeted extractor, not a general protobuf decoder, and pointing at
   `SPEC.md`'s Solution item 1 for the field paths it must support.

## Acceptance

- [ ] `cd agentprof && go test ./internal/antigravity/... -run TestProtowire -v` → all walker unit tests pass (varint decode, nested field path, repeated map field, malformed-input skip, unknown-field skip)
- [ ] `cd agentprof && go vet ./internal/antigravity/...` → clean
- [ ] `cd agentprof && go build ./...` → succeeds (package compiles standalone; no other package references it yet)
