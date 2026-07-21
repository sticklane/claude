Status: draft
Discovered-from: specs/ctxignore-git-overlay/evidence/spec-review.md
Spec: ../SPEC.md
Blocking: no

# Bare (no-trailing-slash) `.ctxignore` directory patterns behave inconsistently between the git overlay and the no-VCS baseline

A bare directory-name pattern with no trailing slash (e.g. `dist`,
`node_modules`, `target`) excludes nothing under the git overlay
(`context-tree/src/vcs/mod.rs:76-85`, via `ctxignore_matches` at
`:250-266`) but prunes the entire subtree in the no-VCS baseline's `walk`.

Mechanism: `ctxignore_matches` only matches the basename for a
slash-less pattern. The overlay tests git's flat FILE paths (e.g.
`dist/lib.py`), so `glob_match("dist", "lib.py")` is false and nothing is
excluded. The no-VCS baseline's `walk` instead hits the `dist`
*directory entry itself*, matches its basename, and prunes the whole
subtree — so the same bare pattern excludes there.

Same `.ctxignore` content, opposite results depending on which VCS mode
is active, and it silently defeats the feature's headline use case
(excluding committed `dist/`/vendored trees) for any user who omits the
trailing slash — the common gitignore-convention form.

Not auto-fixed by the spec-completion review that discovered it: the
correct resolution is a genuine design decision, not a mechanical bug.
The README shipped in ctxignore-git-overlay task 02's diff currently
documents "a pattern with no `/` matches the basename" (ratifying
basename-only), while the baseline behavior and ordinary gitignore user
expectation is directory-pruning. Two resolution options:

(A) Make the overlay's matcher treat a slash-less pattern as matching
any path segment, so bare `dist` prunes `dist/**` under git too (aligns
with gitignore + the baseline; then the README's "matches the basename"
line needs updating to describe the new semantics).

(B) Keep basename-only semantics as documented, and add an explicit
README warning that directory exclusions require a trailing slash
(`dist/`), so users don't silently lose the exclusion.

Fix path is inside `context-tree/src/vcs/mod.rs` (the shared,
pre-existing `ctxignore_matches`) plus `context-tree/README.md` and its
mirrors, all within ctxignore-git-overlay's original Touch footprint.
