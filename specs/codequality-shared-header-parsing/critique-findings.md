# Critique findings — codequality-shared-header-parsing

Verdict: **NOT READY** (drain gen 4 critique intake, 2026-07-12; Run-token e83f34f07094a4fa)

The refactor is worth doing (two divergent `Priority:` regexes + duplicated
`_load_module` are real), but the spec has an unsatisfiable acceptance criterion
and an undisclosed behavior change. Needs a human revision before breakdown.

## Ranked findings (from the critic agent)

1. **Criterion #5 (`diff -r` empty vs mirror) is unsatisfiable for the primary
   file (conf 88).** SPEC.md:73-75 requires every touched `.py` be byte-identical
   to its `antigravity/` counterpart, but `prioritize_scan.py:18` legitimately
   diverges from its mirror (`antigravity/.../prioritize_scan.py:18-20` has an
   adapted standalone-install docstring). CLAUDE.md says the port is skills
   "near-identical," not identical. A drained worker either clobbers the port
   docstring to force an empty diff (silent regression) or stalls. Fix: use the
   repo's content-parity check instead of raw `diff -r`-empty, or state the
   docstring block is the sole permitted divergence.
   (Same false byte-parity assumption as codequality-antigravity-content-parity.)

2. **Loader bootstrap mechanism ambiguous, one reading self-contradicts (conf
   65).** SPEC.md:38-40 says import "the same way viz/spec_readiness are" — but
   those are two different mechanisms (`sys.path.insert`+`import viz` vs
   `_load_module`-by-path). Since the new module CONTAINS `_load_module` and
   criterion #3 forbids a local `def _load_module` in consumers, the path-load
   reading needs a loader to load the loader. Only the viz-style
   `sys.path.insert` + `import headers` is viable. Fix: pin the mechanism to the
   viz pattern explicitly.

3. **"Share the regex" silently widens prioritize's parsing (conf 55).** The
   adopted shared regex is workboard's `\[?(P\d)\]?` (any digit); prioritize's
   current `P[0-3]` matches only P0-P3. After the refactor `Priority: P7` flips
   from `P2 (default)` to `P7`. No criterion catches it. Fix: if P0-3 is the
   invariant, shared regex should be `\[?(P[0-3])\]?`; add a range fixture.

Nit (non-blocking): stale line anchors — `PRIORITY_RE` is workboard.py:237 not
229; `DEPENDS_RE` (236) sits between `STATUS_RE` (235) and `PRIORITY_RE` (237).

## Next step

Human revises SPEC.md: fix criterion #5 to the content-parity check, pin the
loader to the viz import pattern, decide the regex range and test it. Then re-run
/critique. Do not /breakdown until READY.
