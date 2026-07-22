Status: deferred
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

## Deferred questions

The task body itself declares this "a genuine design decision, not a
mechanical bug" and gives two materially different resolutions (A vs B)
without choosing. No `## Answers` section resolves it, and the task carries
no runnable acceptance criteria. An unattended worker cannot pick between
them: the choice sets shipped, user-visible index-membership semantics, and
neither option is a neutral reversible default — one changes behavior, the
other ratifies today's behavior via a user-facing "by design" warning. Per
the drain defer contract ("any ambiguity with no reversible default stops
the worker with DEFERRED"), this is deferred to a human.

**Question:** For a bare (no-trailing-slash) `.ctxignore` directory pattern
(e.g. `dist`), which semantics ship under the git overlay?

- **Option A — segment match (align overlay with baseline + gitignore).**
  Change `ctxignore_matches` so a slash-less pattern matches when ANY path
  segment equals it (glob-aware), so `dist` excludes `dist/lib.py` under git
  too. This makes overlay and no-VCS baseline consistent and matches
  ordinary gitignore expectation. Verified low-risk to R3's
  "baseline byte-identical" gate: the baseline `walk` already prunes at the
  `dist` directory entry before descending, so segment-matching leaves
  baseline output unchanged while only adding matches the git overlay
  currently misses. Requires updating the README/mirror line that currently
  reads "a pattern with no `/` matches the basename" to describe segment
  semantics.

- **Option B — keep basename-only, document the gotcha.** Leave
  `ctxignore_matches` unchanged and add a README (+ `.claude` /
  `antigravity` mirror) warning that directory exclusions require a trailing
  slash (`dist/`), so users don't silently lose the exclusion. Docs-only, no
  behavior change.

**Analysis for the decider:** The governing `../SPEC.md` leans toward B —
R2 pins the grammar as "exactly the shipped matcher" with "pattern without
`/` matches the basename," and Out-of-scope defers "Full gitignore pattern
semantics (`!`, `**`, anchoring subtleties) — the minimal matcher stays
as-is; extend only if a real repo need surfaces." Segment-matching is
exactly such an anchoring subtlety. BUT this task exists *because* that pin
silently defeats the feature's headline use case (excluding committed
`dist/`) for any user who writes the common gitignore form without a
trailing slash — i.e. it argues the "real repo need" threshold is met, which
is what reopens A. That product judgment (is basename-only intended, or a
gap worth extending the matcher for?) is the decision to make.

Touch footprint for whichever option is chosen (both within the original
spec footprint): A → `context-tree/src/vcs/mod.rs` (matcher) +
`context-tree/README.md` + `.claude/skills/ctx/SKILL.md` +
`antigravity/.agents/skills/ctx/SKILL.md` + tests under `context-tree/tests`.
B → `context-tree/README.md` + the two skill mirrors only. Either resolution
should add a test asserting the chosen bare-`dist`-under-git behavior.
