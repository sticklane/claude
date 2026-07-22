# Task 03: `--in` / `--not-in` path-prefix result filters on `refs` and `map`

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->

Status: pending
Depends on: 02
Priority: P2
Budget: 20 turns
Spec: ../SPEC.md (requirement R3)
Touch: context-tree/src/cmd/refs.rs, context-tree/src/cmd/map.rs, context-tree/src/path.rs, context-tree/src/cli.rs, context-tree/src/lib.rs, context-tree/tests/query.rs

## Goal

`refs` and `map` accept repeatable `--in <path-prefix>` and `--not-in
<path-prefix>` flags that filter results by file-path prefix. `refs <sym> --in
go/cmd --not-in attic` returns only references whose path starts with `go/cmd`
and not with `attic`. Filters compose with the existing plain-text and `--json`
output formats.

## Touch

Add the `--not-in` flag (and, for `map`, the `--in` flag) in `cli.rs`; apply a
path-prefix filter to `refs` result rows and to `map`'s ranked output. Reuse /
extend the path-prefix helper in `path.rs`.

`--in` already exists on `refs` from task 02 (as a resolution disambiguator).
This task must reconcile the two meanings coherently against a single
path-prefix helper: `--in`/`--not-in` narrow the emitted result set by owning
file path. Keep task 02's disambiguation behavior intact. Do NOT touch `sig.rs`,
`notes.rs`, `show.rs`, or any `SKILL.md`.

## Steps

1. Write the failing golden tests first in `tests/query.rs` over a fixture with
   the same symbol referenced from both `go/cmd/...` and `attic/...`:
   - `refs <sym> --in go/cmd` → only `go/cmd` paths.
   - `refs <sym> --not-in attic` → excludes `attic` paths.
   - `--in` + `--not-in` compose; repeatable `--in` unions prefixes.
   - The same filter narrows `map` output.
   - Filters apply identically under `--json`.
2. Add `--not-in <path-prefix>` (repeatable) to `Refs` and both `--in`/`--not-in`
   to `Map` in `cli.rs`; thread into `cmd::refs::Args` / `cmd::map::Args`.
3. Add a small path-prefix predicate in `path.rs` (`keep if starts_with any --in
   AND starts_with no --not-in`; empty `--in` = keep-all) and apply it to the
   result rows in `refs.rs` and the ranked entries in `map.rs`, before the
   truncation/limit line so counts reflect the filtered set.
4. Run `bash scripts/check.sh` green.

## Acceptance

- [ ] `cd context-tree && cargo test` → new `--in`/`--not-in` filter golden tests pass
- [ ] `bash context-tree/scripts/check.sh` → exits 0
