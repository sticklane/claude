# Tasks

Larger work lives in `specs/`. Small items live here.

## Open specs (from the 2026-07-04 best-practices review)
- [x] [supported-cli-migration](../specs/supported-cli-migration/SPEC.md) — P1:
      use `claude plugin list --json` (enabled filter, fixes disabled-plugin
      bug) and `claude agents --json` instead of scraping internal files. DONE.
- [x] [internal-format-drift-resilience](../specs/internal-format-drift-resilience/SPEC.md)
      — P2: "source check" health banner, realpath session→repo matching,
      PID-reuse addressed by P1 (CLI is primary). DONE.
- [x] [parser-unit-tests](../specs/parser-unit-tests/SPEC.md) — P2: 17 unit
      tests over the pure parse/layout functions; run by check.sh. DONE.

## Small nits
- [ ] Render footgun (review #6): `tile()`'s `v`, the gchip `{g["dirty"]}`, and
      `readout` interpolate without `esc()` — safe only because callers pass
      ints today. Wrap in `int(...)` at the interpolation site to enforce the
      invariant. Zero-cost, no behavior change.
- [ ] Skills view has no cache; every 25s refresh re-scans the filesystem. A
      short TTL (like the board's) would cut idle load. Low priority (fs-only).
