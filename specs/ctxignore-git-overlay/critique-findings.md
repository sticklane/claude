# Critique findings — READY WITH NITS

SPEC.md-hash: e1a71d4b5b728f209032f93c19e5aac03e6f99c2dc41a4f70f6cf510d72625ae
Critic verdict: READY WITH NITS (settled after 3 rounds, 2026-07-20)

## 2026-07-20 — round 3 (re-check after mechanical fixes)

Verdict READY WITH NITS. All prior-round fixes verified against source:
R3 wrap-site complete (`detect()` at `vcs/mod.rs:48` is the only
construction site; all consumers — `sync/mod.rs:86`, `cmd/at.rs:97`,
`notes/mod.rs:178` — route through it); `user_identity` delegation guard
real (trait default is `None`, `vcs/mod.rs:36`); `at` exit-4 anchor valid
(`EXIT_BAD_POSITION = 4`, ignore branch reached after extension checks);
R4 lazy-sync holds (`run_sync` rebuilds membership every sweep, no
change-feed short-circuit); all R6/R7 grep anchors differ from disk
(non-vacuous).

1. **Nit (confidence 60, applied in-place):** R4 overstated the stale
   outcome — a note in an overlay-excluded file with a byte-identical
   twin (the motivating `dist/`↔`src/` duplication) may legitimately
   re-anchor to the twin rather than go stale. Reworded to "when no
   equivalent symbol remains in the indexed set" per the critic's
   smallest fix. No implementation change; the named test's
   single-location fixture stays correct.

## 2026-07-20 — round 2 (mechanical, all applied)

1. Overlay wrapper could silently regress git note-author identity
   (confidence 78) → R3 now requires verbatim delegation of all
   `VcsAdapter` methods + test `ctxignore_overlay_git_note_author_preserved`.
2. Antigravity mirror + plugin.json bump had no runnable check
   (confidence 72) → added mirror grep and a `0.9.23`-anchored
   version-bump criterion.
3. Composed `is_ignored` untested for `ctx at` (confidence 65) → added
   `ctxignore_overlay_at_excluded_file_exits_4`.

## 2026-07-20 — round 1 (pre-commit, all applied)

1. R3 wrap-site two-implementations-ambiguous (confidence 72) → pinned:
   shared matcher, `detect()` wraps non-baseline adapters only, baseline
   keeps built-in call, structural baseline-unchanged test.
2. Parent SPEC R4/R5 left contradicting shipped behavior (confidence
   68) → new R7 supersession requirement + anchored grep.
3. Notes into newly-ignored files unspecified (confidence 63) → stated
   in R4 + test `ctxignore_overlay_note_goes_stale_not_reanchored`.
