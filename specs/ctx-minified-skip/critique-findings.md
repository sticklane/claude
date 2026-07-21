# Critique findings — NOT READY (2026-07-21, round 1; fixes applied same day, NOT re-verified)

No content hash ON PURPOSE — next /critique must re-run (round-1
verdict was pre-fix; critic unavailable for re-run).

Round-1 findings (all applied):
1. Escape hatch impossible (`!` violates ctxignore subtractive-only
   contract). Fixed: new `.ctxkeep` sibling file, same glob grammar,
   exemption-only semantic; golden asserts it can't resurrect
   ctxignore-excluded paths.
2. 5000-byte constant dead (any >50%-of->50KB line is >25KB). Fixed:
   dropped; second disjunct is now line-count ≤ 5 AND largest line
   >50% of bytes.
3. Embedded-big-literal false positive undecided. Fixed: the ≤5-line
   guard exempts it; R3 fixture (b) pins it.
4. "Candidate file" undefined; .min.css vacuous (no CSS extractor).
   Fixed: candidates = extractor-accepted files; .min.css dropped to
   Non-goals with sourcemaps/JSON.
5. R5 targeted token-doctrine R7 text that hasn't landed. Fixed: hard
   dependency declared; registry SLOT 4.
6. Tree semantics implicit; R4 redundant. Fixed: new file-level output
   class defined (non-candidates stay omitted); R4 merged into R2.
