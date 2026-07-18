# Task 08: LSP enrichment (optional, additive)

Status: done
Depends on: 07
Priority: P2
Budget: 30 turns
Spec: ../SPEC.md (requirement R11)
Touch: context-tree/src/lsp/**, context-tree/src/cmd/refs.rs, context-tree/src/lib.rs, context-tree/Cargo.toml, context-tree/tests/fixtures/lsp/**, context-tree/tests/*.rs

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

- [x] `cd context-tree && cargo test refs_no_lsp` → passes (no LSP
      configured: `heuristic` results, exit 0 — always runnable, not
      manual-pending)
      Evidence: `test refs_no_lsp ... ok` (verifier ran it; evidence/08-lsp-enrichment.md).
- [x] `cd context-tree && cargo test refs_lsp_precise` → passes when a
      language server is available in the environment (`precise` result
      present); if none is installable here, this criterion is
      MANUAL-PENDING (reason: no language server installable in the
      unattended test environment) rather than skipped silently — the
      worker states this explicitly in its final report
      Evidence: `test refs_lsp_precise ... ok`; rust-analyzer 1.97.1 IS
      available, so the live end-to-end `refs_lsp_precise_live` (#[ignore], real
      rust-analyzer) was also run and passed (4.35s). NOT manual-pending.
- [x] `bash context-tree/scripts/check.sh` → exits 0
      Evidence: check.sh exit 0, all suites pass (verifier confirmed).

## Decisions

- Added `pub mod lsp;` to context-tree/src/lib.rs (one line) — beyond the
  declared Touch, but a new module is unreachable without its `mod`
  declaration. Reversible: remove the line (and the module). No new subcommand
  was added, per Goal.
- `refs_lsp_precise` uses a deterministic test double for "a configured
  language server available" (the trait the task's Step 1 designed), so the
  named acceptance test stays reliable in check.sh; the real rust-analyzer path
  is exercised by the #[ignore]d `refs_lsp_precise_live` (slow external dep,
  mocked in the always-run suite per the repo's TDD rules). Reverse by deleting
  the live test / test double.
- Enrichment cache lives at `.context/cache/lsp-enrichment.json` (a JSON
  sidecar, gitignored under the derived cache dir), never a write into the
  shared SQLite index. Reverse by changing `CACHE_FILE` / removing the module.
