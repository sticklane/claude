# Verification: Task 08 — LSP enrichment

Verdict: PASS

## Append-only task-file check

`git diff f0221af -- specs/codebase-context-tree/tasks/08-lsp-enrichment.md`
shows a single 27-line insertion: the `<!-- PLAN (delete at close-out) -->`
comment block, inserted directly after the `Touch:` line. No other line in
the file changed — Goal/Steps/Touch/Budget/Acceptance text is byte-identical
to base. Status line remains `in-progress` and all Acceptance checkboxes
remain unticked (`- [ ]`), i.e. no evidence lines or checkbox ticks were
added either. This is within the allowed set (plan comment block).

Commit that made this change: `3c8563a test: R11 LSP enrichment — trait,
cache, enrich pass + red refs_lsp_precise` (only commit touching the task
file since f0221af).

## Criterion 1 — `cd context-tree && cargo test refs_no_lsp`

Command: `export PATH="$HOME/.cargo/bin:$PATH"; cd context-tree && cargo test refs_no_lsp`

Output (tests/lsp.rs section):

```
running 1 test
test refs_no_lsp ... ok

test result: ok. 1 passed; 0 failed; 0 ignored; 0 measured; 3 filtered out; finished in 0.94s
```

Result: PASS. No LSP cache present → heuristic results, exit 0.

## Criterion 2 — `cd context-tree && cargo test refs_lsp_precise`

Command: `export PATH="$HOME/.cargo/bin:$PATH"; cd context-tree && cargo test refs_lsp_precise`

Output (tests/lsp.rs section):

```
running 2 tests
test refs_lsp_precise_live ... ignored
test refs_lsp_precise ... ok
```

Result: PASS. `refs_lsp_precise` (fake `ReferenceResolver` double, always
run) passes deterministically; `refs_lsp_precise_live` correctly shows
`ignored` under the default (non `--ignored`) run.

### Optional live-path confirmation (ran it)

rust-analyzer 1.97.1 confirmed installed at `~/.cargo/bin/rust-analyzer`.

Command: `cd context-tree && cargo test --test lsp refs_lsp_precise_live -- --ignored`

Output:

```
running 1 test
test refs_lsp_precise_live has been running for over 60 seconds
test refs_lsp_precise_live ... ok

test result: ok. 1 passed; 0 failed; 0 ignored; 0 measured; 3 filtered out; finished in 63.02s
```

Result: PASS. The live rust-analyzer end-to-end path was exercised and
passed (63s, consistent with the documented ~60s workspace-load cost).

## Criterion 3 — `bash context-tree/scripts/check.sh`

Command: `export PATH="$HOME/.cargo/bin:$PATH"; bash context-tree/scripts/check.sh`

Result: exit code 0. Full log tail confirms all test binaries (query,
query_edges, rust, sync, typescript, zig, doc-tests) pass; no failures
reported anywhere in the run (grepped for `FAILED`/non-zero exit — none
found; explicit `echo "EXIT:$?"` printed `EXIT:0`).

## Design verification (Goal honored)

- **Self-contained JSON sidecar, not the shared SQLite index.**
  `context-tree/src/lsp/mod.rs`:
  - `const CACHE_FILE: &str = "lsp-enrichment.json";`
  - `use crate::sync::cache_dir;` — same shared `cache_dir(root)` helper
    used by the SQLite index (`sync::cache_dir` resolves to
    `<root>/.context/cache`), but `EnrichmentCache::write` calls
    `std::fs::write(dir.join(CACHE_FILE), serde_json::to_vec_pretty(&doc)?)`
    — a distinct JSON file (`.context/cache/lsp-enrichment.json`) sitting
    alongside `index.sqlite`, never a write through `IndexStore`/rusqlite.
    `git diff f0221af --stat -- context-tree/src/index` is empty — the
    SQLite index module is untouched.
- **`cmd/refs.rs` consults it through a documented interface.**
  `refs.rs` imports `crate::lsp::EnrichmentCache`, calls
  `EnrichmentCache::load(&root)` once per invocation, and uses
  `cache.is_precise(name, path, line)` (via a small `ref_label` helper) and
  `cache.signature(&qpath)` to decide `precise` vs `heuristic` labels for
  both the plain-text and `--json` renderers. `mod.rs` doc comments name
  `EnrichmentCache::load` / `is_precise` / `signature` explicitly as "the
  documented interface `cmd/refs.rs` [uses]".
- **No cache present ⇒ refs unchanged.** `EnrichmentCache::load` returns
  `None` when the sidecar file is absent; `ref_label`/inline label logic
  fall through to `"heuristic"` in that case — matches criterion 1's
  observed behavior (regression guard, `refs_no_lsp` passes).
- **Untouched files, confirmed by diff:**
  - `git diff f0221af --stat -- context-tree/src/index` → empty (no output)
  - `git diff f0221af --stat -- context-tree/src/notes` → empty (no output)
  - `git diff f0221af --stat -- context-tree/src/cmd/tree.rs context-tree/src/cmd/sig.rs context-tree/src/cmd/at.rs context-tree/src/cmd/deps.rs context-tree/src/cmd/mod.rs` → empty (no output)

## Touch-list conformance

Full diff since f0221af (`git diff f0221af --stat`):

```
context-tree/src/cmd/refs.rs                                 |  54 ++++-
context-tree/src/lib.rs                                       |   1 +
context-tree/src/lsp/client.rs                                | 263 ++++++++
context-tree/src/lsp/mod.rs                                    | 209 ++++++
context-tree/tests/lsp.rs                                      | 191 ++++++
specs/codebase-context-tree/tasks/08-lsp-enrichment.md         |  27 ++
6 files changed, 737 insertions(+), 8 deletions(-)
```

All source changes fall within the declared `Touch:` list
(`context-tree/src/lsp/**`, `context-tree/src/cmd/refs.rs`,
`context-tree/tests/*.rs`) with one exception: `context-tree/src/lib.rs`
(`pub mod lsp;`), which the task's own PLAN comment block flags up front as
"additive, beyond declared Touch — reported in Decisions." This is a
one-line, minimal, unavoidable addition (Rust requires the module
declaration) and is self-disclosed in the task file's plan block itself —
treated as a disclosed, justified, minimal exception rather than
undisclosed scope creep. `Cargo.toml` and `tests/fixtures/lsp/**` (both in
the allowed Touch list) were not modified — no new dependency or fixture
files were needed for this design.

No changes appear outside the Touch list; no changes to specs/**,
docs/**, other task files, AGENTS.md, or README.md were found in the diff.

## Scope-creep / overfitting check

- No test files were modified after being authored — `tests/lsp.rs` was
  added fresh in the single commit `3c8563a` alongside the implementation;
  git log shows no separate later edit to the test file.
- `refs_lsp_precise`'s fake resolver is a legitimate test double for "a
  configured language server available" (the trait `ReferenceResolver` is
  the abstraction under test) — it is not special-cased to the live
  rust-analyzer fixture; the separately-passing `refs_lsp_precise_live`
  test (run above, not skipped) confirms the real integration path also
  works, so the deterministic double is not masking a broken live
  integration.

## Overall verdict: PASS

All three acceptance criteria pass by direct command execution; the
optional live rust-analyzer path also passes. Design matches the stated
Goal (self-contained JSON sidecar, documented cache interface, refs
unchanged with no cache). Touch-list conformance holds except for a single
disclosed one-line `lib.rs` addition. Append-only task-file check holds
(only the plan comment block was added).
