# Task 02: R1 — zone tagging on refs/tree/map (text + `--json`)

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->

Status: done
Depends on: 01
Priority: P1
Budget: 12 turns
Spec: ../SPEC.md (R1)
Touch: context-tree/src/cmd/refs.rs, context-tree/src/cmd/tree.rs, context-tree/src/cmd/map.rs, context-tree/tests/zones_tagging.rs

## Goal

`refs`, `tree`, and `map` annotate any result whose defining file path matches a
`.ctxzones` glob: text output appends `[zone:<label>]` to that result's line, and
`--json` adds a `zone` field (label string) to that result's object. Results not
in any zone are untouched — with zero `.ctxzones` the output of all three
commands (text and JSON) is byte-identical to today.

## Touch

Only the three renderers plus the new test file. Do NOT add CLI flags here
(filtering is task 03); this task is purely additive annotation. `map` ranks by
`SymbolRow` — tag by each symbol's `path` field (already on `SymbolRow`). `tree`
tags both its file-header lines and, in `--json`, each symbol object by
`sym.path`. `refs` tags each `def`/`ref` line and its JSON object by the row's
`path`. Load the `ZoneConfig` once per `render()` from task 01.

## Steps

1. Write failing golden tests first in `context-tree/tests/zones_tagging.rs`
   (model on `tests/ctxignore_overlay.rs`: build a fixture repo with a source
   tree, an in-zone subtree, and a `.ctxzones` mapping e.g. `archived: attic/`;
   drive the built binary via `CARGO_BIN_EXE_ctx`). Assert:
   - `ctx refs <sym>` text: an in-zone `ref`/`def` line ends with
     `[zone:archived]`; a live line has no `[zone:` marker.
   - `ctx refs <sym> --json`: the in-zone reference/definition object has
     `"zone":"archived"`; a live object has no `zone` key.
   - `ctx tree <path>` and `ctx map` text + JSON: same tagging on in-zone
     symbols/files.
   - Zero-`.ctxzones` control: output is identical with and without an empty/
     absent config (no `[zone:` in text, no `zone` key in JSON).
2. Thread `ZoneConfig` through `refs::render`/`render_json`,
   `tree::render`/`render_json`/`render_files`, and `map::render`, tagging each
   emitted line/object whose path resolves to a zone. Keep the JSON key absent
   (not `null`) for live results so the zero-config shape stays byte-for-byte.
3. Run the check script green.

## Acceptance

- [x] `cd context-tree && cargo test --test zones_tagging` → all new tests pass.
      Evidence: 7/7 pass (refs/tree/map text+JSON tagging + zero-config control).
- [x] `cd context-tree && cargo test --test ctxignore_overlay --test query` →
      pre-existing query/overlay goldens still pass (no output regression when no
      `.ctxzones` is present). Evidence: 8/8 overlay + 20/20 query pass.
- [x] `cd context-tree && bash scripts/check.sh` → exits 0. Evidence: full suite
      green (fmt, clippy, all integration tests); CHECK_EXIT=0.
