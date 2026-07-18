# Task 08: LSP enrichment (optional, additive)

Status: in-progress
Depends on: 07
Priority: P2
Budget: 30 turns
Spec: ../SPEC.md (requirement R11)
Touch: context-tree/src/lsp/**, context-tree/src/cmd/refs.rs, context-tree/Cargo.toml, context-tree/tests/fixtures/lsp/**, context-tree/tests/*.rs

<!-- PLAN (delete at close-out)
Design: additive LSP enrichment, no new subcommand.
- src/lsp/mod.rs: `ReferenceResolver` trait (= "a configured language server
  available"), `ResolveTarget`/`PreciseRef`/`Resolved` types, `enrich(root,
  &dyn ReferenceResolver)` (reads index symbols/refs, asks resolver which refs
  are precise, writes a self-contained JSON cache at
  .context/cache/lsp-enrichment.json — NOT the shared SQLite index), and
  `EnrichmentCache::load(root)` + `.is_precise(name,path,line)` +
  `.signature(qpath)` consumed by refs.rs.
- src/lsp/client.rs: `RustAnalyzerResolver` — minimal JSON-RPC-over-stdio LSP
  client (initialize/didOpen/references) implementing the trait for a live
  rust-analyzer.
- src/cmd/refs.rs: consult EnrichmentCache::load(root); a ref/def present in the
  cache renders `precise` (+ resolved signature) instead of `heuristic`; absent
  cache => unchanged heuristic output (never blocks/required).
- lib.rs: `pub mod lsp;` (additive, beyond declared Touch — reported in Decisions).
Tests (tests/lsp.rs):
- refs_no_lsp: no cache => all heuristic, exit 0 (regression guard).
- refs_lsp_precise: fake ReferenceResolver (a configured-server double) => enrich
  => ctx refs shows precise. Deterministic, always green.
- refs_lsp_precise_live: #[ignore] real rust-analyzer end-to-end (run manually,
  reported as evidence). rust-analyzer is external+slow => mocked in the always-run
  suite per TDD rules, live path gated behind --ignored so check.sh stays reliable.
TDD: write tests+lsp module, run refs_lsp_precise RED (refs.rs unmodified still
prints heuristic), then hook refs.rs => GREEN.
-->

## Goal

With a configured language server available, an enrichment pass stores
resolved signatures in a self-contained enrichment cache under `src/lsp/**`
(not the shared SQLite index — task 09 owns the only other in-flight
change to `src/index/**` in this window, and keeping enrichment out of it
avoids a second task needing to touch that schema) and upgrades `ctx refs`
results from `heuristic` to `precise` by having `cmd/refs.rs` consult that
cache through a documented interface. With none configured, every query
still works from syntactic facts alone (this is already true after task 07
— this task must not regress it). LSP enrichment never blocks or is
required for any other command.

## Touch

Only `src/lsp/**` (new) and the minimal hook in `cmd/refs.rs` to consult
enrichment data when present. Do not change `cmd/deps.rs`, `cmd/at.rs`, or
any file under `src/notes/` (task 09, disjoint and safe to run
concurrently with this task).

## Steps

1. Design the enrichment interface: a trait for "a configured language
   server available" that, when present, resolves symbol references and
   stores `precise` labels + resolved signatures in a self-contained
   `src/lsp/**` cache (additive, alongside syntactic facts, never a
   replacement for them) that `cmd/refs.rs` reads through a documented
   interface — not a write into the shared SQLite index.
2. Implement a minimal LSP client sufficient to ask "what are the
   references to this symbol" for at least one language server, if one is
   installable in the current environment (check for e.g. `pyright`,
   `gopls`, `rust-analyzer`, or `typescript-language-server` on PATH).
3. RED/GREEN: with a language server configured, `ctx refs` on a fixture
   symbol returns at least one `precise` result.
4. RED/GREEN: with none configured, `ctx refs` still returns `heuristic`
   results and exits 0 (regression guard against task 07's baseline).
5. If no language server is installable in this unattended test
   environment, do not skip silently: mark the "precise" half of this
   criterion MANUAL-PENDING with the reason stated (no LSP server
   available in this environment), per
   docs/memory/unattended-worker-tool-limits.md, while still shipping and
   testing the "none configured -> heuristic" half.

## Acceptance

- [ ] `cd context-tree && cargo test refs_no_lsp` → passes (no LSP
      configured: `heuristic` results, exit 0 — always runnable, not
      manual-pending)
- [ ] `cd context-tree && cargo test refs_lsp_precise` → passes when a
      language server is available in the environment (`precise` result
      present); if none is installable here, this criterion is
      MANUAL-PENDING (reason: no language server installable in the
      unattended test environment) rather than skipped silently — the
      worker states this explicitly in its final report
- [ ] `bash context-tree/scripts/check.sh` → exits 0
