# Task 04: Golden fixtures + false-positive guards

Status: pending
Depends on: 01, 02, 03
Priority: P1
Budget: 16 turns
Spec: ../SPEC.md (requirements R2, R3)
Touch: context-tree/tests/minified_golden.rs, context-tree/tests/fixtures

## Goal

Committed fixtures + golden tests prove the end-to-end behavior and the
conservative false-negative bias. Skipped fixtures contribute no symbols and
show the tree marker; the three false-positive guard fixtures are NOT
skipped; `.ctxkeep` exempts a minified copy; and `.ctxkeep` cannot resurrect
a `.ctxignore`-excluded path.

## Touch

Adds golden tests and fixture files only — no `src/` changes. If a golden
reveals a behavior gap, the fix belongs in the owning task's file (01/02/03),
not here; this task is fixtures + assertions over already-shipped behavior.

## Steps

1. Commit fixtures under `tests/fixtures/`: (a) a `*.min.js`; (b) a
   generated ≤5-line single-line bundle (> 50 KB, largest line > 50% bytes);
   (c) a normal source file > 50 KB with ordinary line lengths; (d) a source
   file with many ordinary lines plus one embedded > 50%-of-bytes literal
   line; (e) a `.ctxkeep`-matched copy of the minified fixture; (f) a `.md`
   file in the same dir; (g) a `.ctxignore`-excluded path also named in
   `.ctxkeep`.
2. Golden test `map`: output contains none of (a)/(b)'s symbols; contains
   (c)/(d)'s symbols (NOT skipped); contains (e)'s symbols (`.ctxkeep`
   exemption); contains no symbols for (g) (still excluded).
3. Golden test `tree`: (a) and (b) show `(skipped: minified)`; (c)/(d)/(e)
   render normally; (f) `.md` stays unlisted.
4. Golden test asserting `.ctxkeep` does NOT resurrect the
   `.ctxignore`-excluded path (g).

## Acceptance

- [ ] `cd context-tree && cargo test --test minified_golden` → all goldens
  pass: (a)/(b) skipped with marker and zero symbols; (c)/(d) not skipped;
  (e) exempted by `.ctxkeep`; (f) `.md` unlisted; (g) stays excluded.
- [ ] `bash context-tree/scripts/check.sh` → exits 0.
