# Task 01: exact-refs via per-language LSP shell-out (`ctx refs --exact`)

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->

Status: in-progress
Depends on: none
Priority: P1
Budget: 12 turns
Spec: ../SPEC.md (requirement R2; fork F1 decided (i))
Touch: context-tree/src/lsp/, context-tree/src/cmd/refs.rs, context-tree/src/cli.rs, context-tree/tests/lsp.rs, context-tree/README.md

## Goal

`ctx refs --exact` consults a language server when a server binary for the
symbol's language is found, returning compiler-verified references that drop
the `heuristic` tag, and caches results in the index with a generation stamp
that invalidates when the index changes. When no server binary is installed,
`ctx refs --exact` (and plain `ctx refs`) behave byte-identically to today.
This implements F1's decided option (i) — built-in LSP shell-out — by
extending the existing `context-tree/src/lsp/` scaffolding
(`ReferenceResolver` trait, `EnrichmentCache`, `RustAnalyzerResolver`,
`enrich()`) rather than building a new subsystem.

## Touch

In scope: the `context-tree/` Rust crate — the `lsp/` module (add
per-language resolvers, generation stamp), `cmd/refs.rs` (the `--exact`
path and tag selection), `cli.rs` (flag wiring), `tests/lsp.rs` (golden
disambiguation test), and `context-tree/README.md` (document the flag for
crate consumers).

OUT of scope, do NOT touch:
- `.claude/skills/ctx/SKILL.md` and its antigravity mirror — the ctx skill
  body is under a serialization registry (see the Landing order section in
  ctx-skill-token-doctrine's SPEC.md) and is owned by this spec's gated R1/R4
  and by ctx-query-ergonomics R4, not by R2. Editing it here would collide.
- Any second index-exclusion mechanism (that is R5 / ctxignore-git-overlay).

## Steps

1. Read the existing `context-tree/src/lsp/mod.rs`, `lsp/client.rs`,
   `cmd/refs.rs`, and `tests/lsp.rs` to inherit the established
   `ReferenceResolver` + test-double + `#[ignore]`d-live pattern.
2. Write the failing test first, in `tests/lsp.rs`, mirroring the existing
   test-double shape: construct the `main.rodSpecs`-style ambiguity (one
   symbol name defined in two packages) and assert that with a resolver
   available the `--exact` result is disambiguated (references attributed to
   the correct definition, tag `precise`/non-`heuristic`), and that with no
   resolver the output is byte-identical to plain `ctx refs`.
3. Add per-language resolver selection so a Go symbol dispatches to a gopls
   resolver and a TS symbol to a typescript-language-server resolver, each
   gated on `server_binary()`/`available()` exactly like `RustAnalyzerResolver`.
4. Wire the `--exact` flag in `cli.rs` and the `--exact` path in
   `cmd/refs.rs`; on no available server, fall through to the existing
   heuristic path unchanged.
5. Add the generation stamp to the cached enrichment results so a changed
   index invalidates the cache (F1's "cached in the index with a generation
   stamp").
6. Add a live end-to-end test behind `#[ignore]` gated on the server's
   `available()`, following the existing `refs_lsp_precise_live` pattern.
7. Run `cargo fmt`, `cargo clippy`, and the full test suite green.

## Acceptance

Runnable commands (from `context-tree/`):

- [ ] `cargo test --test lsp` → green; includes the new test-double
  disambiguation test proving `--exact` disambiguates a two-package
  same-name symbol and that the no-server path is byte-identical to plain
  `ctx refs`. (L2 — behavioral, no external server needed.)
- [ ] `cargo build --release && ./target/release/ctx refs <heuristic-symbol>`
  with no LSP server on PATH → output unchanged from a pre-`--exact` run
  (every def still tagged `heuristic`, exit 0). (L2 — behavioral fallback.)
- [ ] `cargo clippy --all-targets -- -D warnings` → clean. (L1.)
- [ ] MANUAL-PENDING (privileged): live disambiguation against a real
  server — `cargo test refs_lsp_precise_live -- --ignored` with `gopls` (or
  `typescript-language-server`) installed. A sandboxed/drained worker cannot
  satisfy this (installing a language server is a package-manager/network
  step, `docs/memory/unattended-worker-tool-limits.md`); a human or the
  orchestrator runs it post-merge. Reason: server binary unavailable to the
  worker. This is the behavioral complement to the test-double criterion
  above.
