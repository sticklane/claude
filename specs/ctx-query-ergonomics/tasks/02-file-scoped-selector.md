# Task 02: file-scoped selector `<path>:<name>` + `--in` disambiguation

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->

Status: pending
Depends on: 01
Priority: P1
Budget: 28 turns
Spec: ../SPEC.md (requirement R1)
Touch: context-tree/src/path.rs, context-tree/src/cmd/sig.rs, context-tree/src/cmd/refs.rs, context-tree/src/cmd/show.rs, context-tree/src/cmd/notes.rs, context-tree/src/cli.rs, context-tree/src/lib.rs, context-tree/tests/query.rs

## Goal

`sig`, `refs`, `show`, and `notes` accept a file-scoped selector
`<path>:<name>` (e.g. `go/cmd/mlhybrid/main.go:rodSpecs`) and a repeatable
`--in <path-prefix>` disambiguating flag, both of which narrow C3 suffix
resolution to symbols in the named file / under the named prefix. For the
two-`main.rodSpecs` fixture shape, the file-scoped form returns exactly one
result, and the bare form's ambiguity listing gains a "rerun with" hint line
showing the file-scoped form for each candidate.

## Touch

Add a shared selector parse + filter helper to `path.rs` (one place, reused by
all four verbs — avoids each verb re-deciding selector semantics). Wire the
`--in` flag and hint line into `sig.rs`, `refs.rs`, `show.rs`, `notes.rs`, the
`Command` enum (`cli.rs`), and dispatch (`lib.rs`).

Do NOT touch `map.rs` — `--in`/`--not-in` result filtering on `map`/`refs` is
task 03. Do NOT touch any `SKILL.md` (task 04). This task shares `cli.rs` /
`lib.rs` / `refs.rs` with tasks 01 and 03 but runs serially after 01 and before
03, so there is no concurrent write.

## Steps

1. Write the failing golden tests first (insta snapshots) in `tests/query.rs`,
   using a fixture with two symbols sharing one qpath in different files (the
   `main.rodSpecs` collision shape):
   - `<path>:<name>` (and `--in <prefix>`) returns exactly one result and exits 0.
   - The bare ambiguous form still exits 3 AND its candidate listing now includes,
     per candidate, a rerun hint printing the file-scoped `<path>:<name>` form.
   - Repeat the selector-resolves-uniquely assertion for each of `sig`, `refs`,
     `show`, `notes` (a representative test per verb is sufficient).
2. In `path.rs`, add a helper that: splits a query into optional `<path>` prefix
   (everything before the last `:` when it names a real path component) and
   `<name>`, and filters the `resolve_suffix` candidate set by owning file path
   (exact file for `<path>:<name>`, prefix for `--in`). Keep it pure and unit-
   tested. Preserve the existing bare-name behavior when no selector/flag is given.
3. Add a repeatable `--in <path-prefix>` arg to `Sig`, `Refs`, `Show`, and the
   `notes` show/add forms in `cli.rs`; thread it into each `cmd::*::Args` and
   apply the helper before/around `resolve_suffix`.
4. In each verb's ambiguity branch, append the per-candidate rerun-hint line
   (both the plain-text and `--json` paths, matching the existing candidate
   shape).
5. Run `bash scripts/check.sh` green; review new snapshots with `cargo insta`
   if the repo uses it, else assert structural output directly.

## Acceptance

- [ ] `cd context-tree && cargo test` → new selector + ambiguity-hint golden tests pass
- [ ] `bash context-tree/scripts/check.sh` → exits 0
