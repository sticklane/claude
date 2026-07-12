# Critique findings — codequality-antigravity-content-parity

Verdict: **NOT READY** (drain gen 4 critique intake, 2026-07-12; Run-token e83f34f07094a4fa)

The spec's central premise is factually false, which makes an acceptance
criterion unsatisfiable and the proposed gate a false-positive machine. Needs a
human spec revision before breakdown.

## Ranked findings (from the critic agent)

1. **The "every other .py is byte-identical" premise is false (conf 95).**
   SPEC.md:21-23 claims all other mirrored `.py` files are byte-identical, so
   byte-parity is the de-facto contract. Diffing all 10 mirrored `.py` files shows
   FOUR differ, not one:
   - `_shared/test_viz.py` — real drift (correctly identified target).
   - `prioritize/prioritize_scan.py` — legitimate port (standalone-install docstring).
   - `list-specs/test_list_specs.py` — legitimate port (`.agents/skills/` run path).
   - `prioritize/test_prioritize_scan.py` — legitimate port (`.agents/skills/` path).
   The Approach-2 gate (`diff -q` over every `.py`) flags all three legitimate
   ports → can never go green. Criterion 3 ("exits 0 with no output on the fixed
   tree") is impossible after Approach step 1 copies only test_viz.py. A drain
   worker either stalls or "fixes" it by clobbering the antigravity run-path
   adaptations and standalone docstring — breaking the port to satisfy a byte
   diff. Fix: scope the gate to files that are contractually byte-identical
   (include-list, e.g. `_shared/*.py`, `workboard/*.py`, `list-specs/list_specs.py`)
   OR normalize sanctioned adaptations before diffing; and correct the false
   premise.

2. **The un-greenable gate poisons the repo's canonical check loop (conf 90).**
   Criterion 5 (SPEC.md:60-61) runs the AGENTS.md:37 test loop and requires no
   FAIL lines. Dropping the mis-scoped gate into `tests/` red-bars EVERY run of the
   repo's test surface, not just this criterion. Same fix as #1; raised separately
   for blast radius.

3. **Criterion 1's "pre-fix tree or a fixture" is underspecified (conf 65).**
   SPEC.md:51-53 wants the gate to flag `_shared/test_viz.py` before the fix, but
   after the copy the pre-fix tree is gone; a post-fix verifier cannot reproduce
   it. Engineers diverge (git stash vs committed fixture vs skip) — stall risk for
   an unattended worker. Fix: name the mechanism, e.g. a committed
   `tests/fixtures/` divergent pair the gate asserts against (permanent,
   order-independent).

## Next step

Human revises SPEC.md: correct the byte-identical premise, scope the gate to the
contractually-identical file set (or add a normalization), and pin criterion 1 to
a committed fixture. Then re-run /critique. Do not /breakdown until READY.

Note: the drift the spec targets is real — `.claude/skills/_shared/test_viz.py`
(210 lines) has a `test_viz_axis_labels_carry_muted_tint_with_token_fallback`
method the antigravity mirror (198 lines) is missing. A correctly-scoped version
of this spec is worth building.
