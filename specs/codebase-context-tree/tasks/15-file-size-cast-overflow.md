Status: draft
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

- [ ] A new test whose name contains `size_above_i64_max` (phrase absent
      from `context-tree/` today, verified 2026-07-19) round-trips a
      file size greater than `i64::MAX` through the index layer's
      store/load path (`upsert_file` → the prev-state read) and asserts
      the size survives unchanged — the behavior whose corruption would
      break size-based staleness detection. Red-first per
      `.claude/rules/quality-discipline.md`: it must fail against
      today's `as i64`/`as u64` round-trip before the fix.
- [ ] `bash context-tree/scripts/check.sh` exits 0 (the crate's
      documented canonical check: `cargo fmt --check`, `cargo clippy
    --all-targets -- -D warnings`, `cargo test` — which picks the new
      test up with no wiring).
