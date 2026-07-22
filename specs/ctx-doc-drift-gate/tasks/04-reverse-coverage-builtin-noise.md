Status: done
Discovered-from: specs/ctx-doc-drift-gate/tasks/01-conformance-test.md
Spec: ../SPEC.md
Blocking: no

# Reverse-coverage report lists universal clap built-ins as undocumented noise

The reverse-coverage report (R3, non-gating) emitted by
`context-tree/tests/doc_conformance.rs::compute_reverse_coverage` lists
`--help`/`--version` as "undocumented" on every subcommand, diluting the
real under-claimed capabilities (e.g. `tree --depth`, `refs --limit`,
`map --doc`, `--no-sync`). A one-line filter for clap's universal built-ins
would sharpen the report but is behavior-altering post-verification, so it
was left as-is by task 01's worker.

## Acceptance

`compute_reverse_coverage` in `context-tree/tests/doc_conformance.rs` skips
clap's universal built-in flags (`--help`, `--version`) so they never appear
in the R3 reverse-coverage report, sharpening it down to genuinely
under-claimed capabilities. Run from `context-tree/`:

- [x] A guard test asserts the report lists no `--help`/`--version` entry:
  `cargo test --test doc_conformance reverse_coverage_excludes_clap_universal_builtins`
  passes (it fails red without the filter — the built-in noise was 16 of 57
  entries).
- [x] The whole conformance suite stays green:
  `cargo test --test doc_conformance` → 6 passed, 0 failed.
- [x] Real under-claimed flags survive the filter: the report still lists
  `map --doc`, `refs --limit`, and the `--no-sync` rows
  (`cargo test --test doc_conformance docs_conform_to_binary_with_seeded_waivers -- --nocapture`
  shows 41 undocumented entries, down from 57, with zero `--help`/`--version`).
- [x] Crate lints clean: `cargo fmt --check` and `cargo clippy --tests`
  report no warnings.

Out of scope: the stale `show` waiver (task 01's `Waiver { subcommand:
"show", flag: None }`) is a sibling R1-waiver concern owned elsewhere, not
this report-filter task — left untouched.
