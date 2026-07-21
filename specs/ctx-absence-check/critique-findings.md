# Critique findings — NOT READY (2026-07-21, round 1; fixes applied same day, NOT re-verified)

No content hash ON PURPOSE — next /critique must re-run (round-1
verdict was pre-fix; critic unavailable for re-run).

Round-1 findings (all applied):
1. SEVERE: exemplar grep used brace expansion in --include — verified
   live to return zero matches (BSD grep + ugrep), i.e. the tool would
   have mechanized false absence. Fixed: repeated --include flags,
   plus a golden asserting no brace pattern in suggested_check.
2. "Near-miss retained" — nothing exists to retain (sig.rs:76,
   refs.rs:107 print one line and exit). Fixed: "ADDED (new
   behavior)" with the verification cited.
3. Blast radius unstated (stderr/exit/JSON error shape/MCP render()).
   Fixed: full surface contract pinned — append to stderr, exit
   unchanged, JSON EXTENDS legacy error object, MCP golden required.
4. R1 covered `show` which doesn't exist yet. Fixed: ordering after
   query-ergonomics R2, same-or-later task.
5. Language≠extension conflation. Fixed: extractor extension-list
   mapping, union asserted in fixture.
6. -m1 no-op with -l. Fixed: dropped, rationale stated. Registry SLOT
   6; dead-code-zones seam sentence mirrored.
