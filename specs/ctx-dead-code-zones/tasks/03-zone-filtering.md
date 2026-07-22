# Task 03: R2/R3 — zone filtering (`--zone`, `--live-only`) on refs and map

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->

Status: pending
Depends on: 01, 02
Priority: P3
Budget: 14 turns
Spec: ../SPEC.md (R2, R3)
Touch: context-tree/src/cli.rs, context-tree/src/cmd/refs.rs, context-tree/src/cmd/map.rs, context-tree/src/cmd/mod.rs, context-tree/tests/zones_filter.rs

## Goal

`refs` and `map` gain two composable, mutually-exclusive-per-invocation filters:
`--zone <label>` keeps only results in that zone; `--live-only` excludes all
zoned results. An undeclared `--zone` label errors (exit 2) with a message
listing the declared labels. Crucially, `refs <sym> --live-only` that filters
away every reference of a symbol whose references are ALL in-zone emits a
one-line tail `N references exist only in zones: <labels>` and exits 0 — it does
NOT emit the `no_match` boundary (resolution succeeded; only filtering emptied
the set), and it is never a bare empty result.

## Touch

Add the two flags to the `Refs` and `Map` variants in `src/cli.rs` and thread
them into each command's `Args`. Implement the filter + tail in `refs.rs` and
`map.rs`. If a new named exit constant reads cleaner than reusing the literal `2`,
add it to `src/cmd/mod.rs` alongside the existing `EXIT_*` consts (value 2).
Do NOT change `tree` (R2 scopes filtering to refs and map only). Do NOT alter the
`no_match` seam in `src/cmd/no_match.rs`.

## Composition note (name the ordering — spec R2)

`--in/--not-in` (specs/ctx-query-ergonomics R3) do not exist yet. `--zone` /
`--live-only` are independent AND-filters applied to the already-resolved result
vector, so they compose order-independently with the path filters whenever that
sibling spec lands — neither must land first. Implement the zone filters
standalone; do not couple to `--in/--not-in`.

## Steps

1. Write failing golden tests first in `context-tree/tests/zones_filter.rs`,
   naming each R3 command in both text and `--json` (fixture where a symbol's
   every reference is in-zone):
   - `ctx refs <sym>` — plain: shows the in-zone refs (tagged, from task 02),
     exit 0.
   - `ctx refs <sym> --live-only` — text: no `ref` lines, a
     `N references exist only in zones: archived` tail on stderr, exit 0;
     `--json`: `references` empty and a note field carrying the same fact,
     exit 0. Assert it is NOT the `no_match` boundary/error shape.
   - `ctx refs <sym> --zone archived` — only in-zone refs, exit 0.
   - `ctx refs <sym> --zone nosuchlabel` — exit code 2, stderr lists the
     declared labels.
   - Contrast: `ctx refs <trulyMissingSym>` still exits nonzero with the
     `no_match` boundary (regression guard on the seam).
   - `ctx map --live-only` and `ctx map --zone archived` filter the ranked
     set correctly (text + JSON).
2. Add flags to `cli.rs`; thread into `refs::Args` / `map::Args` and the
   dispatch in `src/main.rs` if it constructs the `Args` (check and update
   there if needed — it is within this task's intent even though not listed;
   if `main.rs` must change, add it to Touch before editing).
3. Implement filtering + the filtered-empty tail (build the tail string once,
   share it between the stderr line and the JSON `note` field, mirroring the
   existing `zero_refs_note` pattern in `refs.rs`).
4. Implement unknown-label validation (exit 2, message lists
   `ZoneConfig::declared_labels()`).
5. Run the check script green.

## Acceptance

- [ ] `cd context-tree && cargo test --test zones_filter` → all new tests pass.
- [ ] `cd context-tree && cargo test --test zero_result_tails` → the no-match /
      zero-result seam tests still pass (filtered-empty must not be misread as
      no-match).
- [ ] `cd context-tree && bash scripts/check.sh` → exits 0.
