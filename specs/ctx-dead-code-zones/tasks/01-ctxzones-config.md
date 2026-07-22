# Task 01: `.ctxzones` config + zone-resolver core

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->

Status: in-progress
Depends on: none
Priority: P0
Budget: 8 turns
Spec: ../SPEC.md (Solution: `.ctxzones` grammar; foundation for R1/R2/R3)
Touch: context-tree/src/zones.rs, context-tree/src/lib.rs, context-tree/src/vcs/mod.rs, context-tree/tests/zones_config.rs

## Goal

A new `context-tree/src/zones.rs` module loads `.ctxzones` from the repo root and
resolves a relative path to at most one zone label. It reuses the existing
`.ctxignore` glob matcher verbatim (no new glob syntax) and exposes the two
lookups every later task needs: `zone_of(rel) -> Option<&str>` (first-match-wins
single tag) and `declared_labels() -> Vec<&str>`. Zero `.ctxzones` present → zero
zones (every `zone_of` returns `None`). This task ships the config layer only; no
command output or CLI flag changes yet.

## Touch

`src/zones.rs` is new. In `src/vcs/mod.rs`, promote the existing `glob_match`
(and, if convenient, `ctxignore_matches`) to `pub(crate)` so `zones.rs` reuses
the SAME matcher rather than copying it — do NOT fork a second glob
implementation. `src/lib.rs` gains the `pub mod zones;` declaration. Do NOT touch
any `src/cmd/*.rs` renderer or `src/cli.rs` in this task.

## Steps

1. Write the failing tests first in `context-tree/tests/zones_config.rs`
   (build a temp dir with a fixture `.ctxzones`, load it, assert resolution).
   Cover the line-grammar edges the spec pins:
   - `<label>: <glob>` per line; label charset `[a-z0-9-]+`; blank and `#`
     comment lines skipped.
   - The same label on multiple lines unions its globs.
   - When two different labels both match one path, the first line in file
     order wins (a path carries a single tag).
   - `zone_of` on a path matching no glob returns `None`.
   - Zero `.ctxzones` file → `declared_labels()` empty, all `zone_of` `None`.
   - A malformed line (no `:` separator, or an out-of-charset label) is
     skipped rather than aborting the load (pick and assert one defined
     behavior; document it in a code comment).
2. In `src/vcs/mod.rs`, change `glob_match` (and the helper it needs) from
   private to `pub(crate)`.
3. Implement `src/zones.rs`: a `ZoneConfig` holding ordered `(label, glob)`
   entries parsed from `.ctxzones`, `zone_of(&self, rel: &str) -> Option<&str>`
   returning the first entry whose glob matches (reusing the shared matcher and
   the same basename-vs-full-path semantics `.ctxignore` uses), and
   `declared_labels(&self) -> Vec<&str>` (dedup, declaration order).
4. Add `pub mod zones;` to `src/lib.rs`.
5. Run the check script green.

## Acceptance

- [ ] `cd context-tree && cargo test --test zones_config` → all new tests pass.
- [ ] `cd context-tree && grep -n 'pub(crate) fn glob_match' src/vcs/mod.rs` →
      the matcher is shared, not re-implemented in `zones.rs`
      (`grep -c 'fn glob_match' src/zones.rs` → `0`).
- [ ] `cd context-tree && bash scripts/check.sh` → exits 0 (fmt, clippy, tests).
