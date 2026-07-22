# Task 03: `.ctxkeep` escape hatch

Status: deferred
Depends on: 01
Priority: P2
Budget: 12 turns
Spec: ../SPEC.md (requirements R1, R3)
Touch: context-tree/src/minified.rs, context-tree/src/vcs/mod.rs, context-tree/tests/ctxkeep.rs

## Goal

A new optional sibling file `.ctxkeep` (same glob grammar as `.ctxignore`,
reusing the existing matcher) exempts matching paths from minified
auto-skip. A `.ctxkeep`-matched candidate is parsed normally even when it
would classify as minified. `.ctxkeep` is exemption-only: it is NOT a
general re-include and CANNOT resurrect a path excluded by `.ctxignore`
membership.

## Touch

Adds a `.ctxkeep` loader in `src/vcs/mod.rs` reusing `load_ctxignore`'s
sibling-read shape and the `ctxignore_matches` / `glob_match` matcher (do
not fork a second matcher). Wires the exemption gate into the skip decision
in `src/minified.rs` (the seam task 01 left). Does NOT touch tree output
(task 02) or the index schema. `.ctxkeep` never widens the VCS file list —
it only gates auto-skip, so it must live outside `CtxignoreOverlay`'s
subtractive path.

## Steps

1. Write failing tests in `tests/ctxkeep.rs`: (a) a `.ctxkeep` matching a
   minified fixture → that file parses (symbols present, not skipped);
   (b) a path excluded by `.ctxignore` AND named in `.ctxkeep` stays
   excluded (`.ctxkeep` does not resurrect it).
2. Add `load_ctxkeep(root)` + a `ctxkeep_matches(path)` helper in
   `src/vcs/mod.rs` reusing the existing matcher functions.
3. In `src/minified.rs`'s classify/skip path, short-circuit to NOT-skipped
   when the path matches `.ctxkeep` — but only for the minified-skip
   decision, leaving `.ctxignore` membership untouched (membership is
   decided upstream in the VCS file list, so `.ctxkeep` never sees an
   already-excluded path as a candidate).

## Acceptance

- [ ] `cd context-tree && cargo test --test ctxkeep` → `.ctxkeep`-matched
  minified fixture parses (symbols present); `.ctxignore`-excluded path
  named in `.ctxkeep` stays excluded.
- [ ] `bash context-tree/scripts/check.sh` → exits 0.

## Deferred questions

**Contradicts-premise: true**

- Artifact: this file (`specs/ctx-minified-skip/tasks/03-ctxkeep-escape-hatch.md`)
- Contradicted clause (verbatim, from `## Touch` above): "Wires the
  exemption gate into the skip decision in `src/minified.rs` (the seam
  task 01 left)."
- Evidence: the dispatched worker traced the actual skip decision to its
  one callsite — `context-tree/src/sync/mod.rs:186`
  (`if let Some(reason) = minified::classify(rel, &content)`) — and found
  task 01's own seam comment sits at `sync/mod.rs:183`, not in
  `minified.rs`. `classify(rel, content)` takes no `root` parameter, so it
  cannot load `.ctxkeep` itself; changing its signature would also break
  the two existing callers (`sync/mod.rs` and `tests/minified.rs`), both
  outside this task's `Touch`. `../SPEC.md`'s Parallelization line repeats
  the same wrong location.

**Question:** should this task's `Touch:` be expanded to include
`context-tree/src/sync/mod.rs` (the actual skip-decision seam), so the
`.ctxkeep` gate can be wired at the real callsite? The worker's
ready-to-apply design once expanded: `src/vcs/mod.rs` gets
`load_ctxkeep(root)` mirroring `load_ctxignore`'s sibling-read, reusing
`ctxignore_matches`/`glob_match`; `sync/mod.rs:186` gates the skip
decision itself (a `.ctxkeep`-matched path falls through to the extractor
even when `classify` returns `Some(reason)`); `tests/ctxkeep.rs` gets an
end-to-end `run_sync` test plus the `.ctxignore`-wins-over-`.ctxkeep` test.
This is safe against the sibling task 02 dispatched concurrently in this
same wave (touches `cmd/tree.rs` + `index/mod.rs` only — no overlap with
`sync/mod.rs`).
