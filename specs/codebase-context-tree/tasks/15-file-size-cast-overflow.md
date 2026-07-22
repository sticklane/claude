Status: obsolete
Discovered-from: specs/codebase-context-tree/evidence/spec-review.md
Spec: ../SPEC.md
Blocking: no

# File-size cast overflow in staleness detection

A u64->i64->u64 round-trip for file sizes in context-tree/src/index/mod.rs:291
and context-tree/src/sync/mod.rs:312 overflows above i64::MAX (~9.2
exabytes), which would corrupt size-based staleness detection. Practically
unreachable for any real file, so left unfixed by the spec-completion
review — flagged for a human to judge whether a defensive fix is worth it.

## Acceptance

Site note (verified 2026-07-19): the live casts are
`context-tree/src/index/mod.rs:291` (`size: size as u64` on read) and
`:312`/`:323` (`size as i64` on write); the body's
`sync/mod.rs:312` pointer is stale — that file is 302 lines and casts
only time values.

- [ ] ~~A new test whose name contains `size_above_i64_max`... Red-first...~~
      Not satisfiable — see `## Deferred questions` below. No fix exists to
      write a red-first test against.
- [x] `bash context-tree/scripts/check.sh` exits 0 (unaffected — no source
      bug to fix; a non-red-first regression guard was added instead, see
      `## Closed` below).

## Closed

**Won't-fix / not-a-bug**, resolved by the drain orchestrator directly (a
factual/mathematical question, not a product-design judgment call — see
the two independent empirical confirmations below). Option (a) from the
worker's own recorded recommendation.

Two independent parties confirmed the `u64 -> i64 -> u64` round-trip is
lossless for every value, including sizes above `i64::MAX`, with real
executed tests (not just documented reasoning):
- The dispatched worker ran the exact test criterion 1 asked for against
  unchanged code; it passed green, so the required red-first premise was
  unsatisfiable.
- An independent verifier compiled and ran a throwaway `rustc` test
  sweeping values up to `u64::MAX`, confirmed the two write/read call
  sites really do use plain `as i64`/`as u64` (not `try_into`), and
  confirmed SQLite's INTEGER storage class round-trips the full signed
  64-bit range losslessly.

Added `file_size_above_i64_max_round_trips_losslessly` to
`context-tree/src/index/mod.rs`'s test module as a **guard, not a
red-first regression test** — it already passes today; it exists to catch
a future well-meaning "defensive" saturating/checked cast that would
clamp large sizes and introduce the exact data loss the current
bit-preserving cast avoids. `bash context-tree/scripts/check.sh` re-run
green with the guard test included.
