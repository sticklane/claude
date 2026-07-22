Status: done
Discovered-from: specs/codebase-context-tree/evidence/capability-shakedown-2026-07-20.md
Spec: ../SPEC.md
Blocking: no

# ctx map ranking surfaces bash test locals above real API symbols

On a real repo (this toolkit's own tree), `ctx map`'s top entries are bash
test-scratch variables (`hooks.plugin-autorefresh.test.t#1`…`#10`) ranked
ahead of genuine classes/functions; the demo fixture ranks cleanly. The
ranking should down-weight `variable`-kind symbols — bash locals and
`#N`-suffixed duplicate names especially — relative to functions, classes,
and methods. (Capability-shakedown finding, 2026-07-20; vet/rewrite before
promoting.)

## Approach

Root cause (confirmed empirically): `ctx map` ranks purely by reference
count, and `IndexStore::reference_counts` groups references by **bare name**.
A bash scratch variable reused at top level dedups into `t#1`/`t#2`/`t#3`
(C1 `#<n>` disambiguator), and every dedup copy inherits the full aggregate
count of the common short name `t` — so a handful of scratch locals each
carry a large count and crowd real functions/classes out of the top.

Fix: rank by a kind tier first, then the existing reference-count-then-qpath
order within each tier. The API surface (functions, classes, methods, and
every non-`variable` kind) leads; `variable`-kind symbols are down-weighted
below it; and a duplicate-name `#N`-suffixed qpath sinks below its
un-suffixed peers within each tier (`src/cmd/map.rs::rank_tier`). The
intra-tier order is unchanged, so the demo fixture and the existing
reference-count ranking test still hold.

## Acceptance

- [x] `cargo test --test query map_ranks_functions_above_high_ref_scratch_variables`
  passes — a bash file with a reused top-level scratch variable (`t#1..t#3`,
  each inheriting refs=5 from the common name) ranks `real_api` above every
  `variable lib.t#N` line.
- [x] `cargo test --test query map_ranking_orders_by_reference_count_not_alphabetical`
  still passes — within the (all-function) tier, reference-count order is
  unchanged.
- [x] `bash scripts/check.sh` is green (cargo fmt --check, clippy -D warnings,
  full `cargo test`) — no regression in the demo-fixture map or snapshot
  tests.
