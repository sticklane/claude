# Task 02: ctx tree --files listing mode

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch, Rigor) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Priority values run P0 (highest) through P3; the header is optional — absent means P2. -->
<!-- Status vocabulary: pending → in-progress → done; also blocked (always with an Unblock: line), deferred, skipped, draft (stub awaiting promotion), and needs-verification (implementation complete, acceptance unverified — the verifier flips it to done; scanners treat it as open agent-bounded work, never a needs-attention flag). -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers, in every task file — and ## Progress / ## Deferred questions are drain-written sections (single writer, main checkout): workers report that content, never write it. -->

Status: pending
Depends on: none
Priority: P2
Budget: 10 turns
Spec: ../SPEC.md (requirement R2)
Touch: context-tree/src/cmd/tree.rs, context-tree/src/cli.rs, context-tree/tests/tree_files_mode.rs

## Goal

`ctx tree --files <path>` emits one indexed file path per line with no
symbol lines (`--json`: an array of paths), answering "which files are
under X" without awk pipelines or find cross-checks. In this mode
`--depth` means directory levels below `<path>` (files directly in
`<path>` = depth 1, one subdirectory down = depth 2; relative to the
query path, never the index root — consistent with the existing
"top-level is depth 1" convention). Emitted-path count equals the
index's file membership under the path.

## Touch

`cli.rs` gains only the `--files` flag on the tree subcommand; do NOT
touch refs.rs/deps.rs/no_match.rs (task 01). Symbol-mode `tree` output
is byte-unchanged when `--files` is absent — pin with a golden.

## Steps

1. Failing goldens first (new `tests/tree_files_mode.rs`, fixture
   directory where file count ≠ tree line count today, with nested
   subdirectories): files-only lines, no symbol lines; `--json` array;
   `--depth 1` vs `--depth 2` boundary per the definition above; count
   equals index membership under the path.
2. Implement `--files` in tree.rs; keep symbol-mode output unchanged
   (golden pins the default mode byte-stable on the fixture).
3. fmt + clippy clean.

## Acceptance

- [ ] `cd context-tree && cargo test --test tree_files_mode` → exit 0, covering: files-only output, --json array, --depth 1/2 directory-level semantics, membership count equality, default symbol mode unchanged
- [ ] `cd context-tree && cargo test` → exit 0
- [ ] `cd context-tree && cargo clippy --tests -- -D warnings` → exit 0
