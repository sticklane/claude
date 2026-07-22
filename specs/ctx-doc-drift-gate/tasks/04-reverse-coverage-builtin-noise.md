Status: pending
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

<!-- draft: needs runnable criteria before promotion -->
