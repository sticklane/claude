# Task 01: Fix _shared/test_viz.py drift and add the content-parity gate

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Priority values run P0 (highest) through P3; the header is optional — absent means P2. -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers, in every task file — and ## Progress / ## Deferred questions are drain-written sections (single writer, main checkout): workers report that content, never write it. -->

Status: done
Depends on: none
Priority: P2
Budget: 16 turns
Spec: ../SPEC.md (Approach steps 1-3; all acceptance criteria)
Touch: antigravity/.agents/skills/_shared/test_viz.py, tests/test_antigravity_content_parity.sh, tests/fixtures/content-parity/claude-side/example.py, tests/fixtures/content-parity/antigravity-side/example.py, AGENTS.md

## Goal

Real mirror drift (`_shared/test_viz.py` missing a test method on the
antigravity side) is fixed, and a new content-parity gate exists that
would have caught it — scoped to the narrow set of `.py` files that are
contractually byte-identical across `.claude/skills/` and
`antigravity/.agents/skills/`, proven against a committed divergent
fixture pair, and wired into the repo's `tests/test_*.sh` loop without
breaking the existing existence-only gate.

## Touch

- `antigravity/.agents/skills/_shared/test_viz.py` — mirror-only fix:
  copy the missing `test_viz_axis_labels_carry_muted_tint_with_token_fallback`
  method (and only what's needed to make the file byte-identical to
  `.claude/skills/_shared/test_viz.py`) across. Do not touch `viz.py` on
  either side — it is already byte-identical.
- `tests/test_antigravity_content_parity.sh` — new gate script.
- `tests/fixtures/content-parity/claude-side/example.py` and
  `tests/fixtures/content-parity/antigravity-side/example.py` — new,
  permanent, deliberately-divergent fixture pair (do not model these on
  the pre-fix tree; author them fresh so they never need updating as the
  real tree changes).
- `AGENTS.md` — only if the Commands loop needs a one-line mention; the
  loop (`for t in tests/test_*.sh`) already picks up new scripts by glob,
  so this is verification, not necessarily an edit — confirm before
  changing anything here.

**Do not touch** `tests/test_antigravity_parity.sh` (the existing
existence-only gate — out of scope per SPEC.md) or any `.py` file outside
the include-list below.

## Steps

1. Fix the drift first: diff
   `.claude/skills/_shared/test_viz.py` against
   `antigravity/.agents/skills/_shared/test_viz.py` to find the actual
   current difference (don't assume the line numbers cited in SPEC.md's
   Problem section are still exact), then copy the missing content across
   so the two files are byte-identical. Confirm with
   `diff .claude/skills/_shared/test_viz.py antigravity/.agents/skills/_shared/test_viz.py`
   exiting 0.
2. Determine the actual include-list by globbing both trees:
   `_shared/*.py`, `workboard/*.py`, and `list-specs/list_specs.py` under
   `.claude/skills/` and their mirrors under `antigravity/.agents/skills/`
   (find the real current file lists — do not assume a fixed count).
   Confirm every file in this list is byte-identical after step 1 (this
   is the "contractually-identical subset" SPEC.md's Problem section
   names — `prioritize/*.py` and `list-specs/test_list_specs.py` are
   explicitly OUT because they carry sanctioned port adaptations; do not
   add them).
3. Write `tests/fixtures/content-parity/claude-side/example.py` and
   `tests/fixtures/content-parity/antigravity-side/example.py`: two small
   Python files with deliberate, permanent content divergence (e.g. one
   extra line or a differing docstring) — not derived from any real
   mirrored file, so they never drift with the real tree.
4. Write `tests/test_antigravity_content_parity.sh`: for each file in the
   include-list, `diff -q .claude/skills/<path> antigravity/.agents/skills/<path>`,
   printing each divergent path and exiting nonzero on any difference.
   Give the script a fixture-redirect seam (env var or `--fixture` flag)
   that, when set, points the **compared file set** at
   `tests/fixtures/content-parity/claude-side/` and
   `tests/fixtures/content-parity/antigravity-side/` instead of the real
   include-list — i.e. the flag must swap which files get compared, not
   just which root paths get diffed, so pointing it at the fixture
   actually compares `example.py` against `example.py`. Verify this
   redirect exits nonzero and names `example.py` when invoked against the
   fixture.
5. Confirm `tests/test_antigravity_parity.sh` (the existing existence gate)
   is untouched and still exits 0.
6. Wire into the Commands loop: check whether `AGENTS.md`'s test loop
   (`for t in tests/test_*.sh`) picks up the new script automatically via
   glob (it very likely does — confirm, don't assume) or needs an
   explicit mention; edit `AGENTS.md` only if verification shows it's
   needed.
7. Run `for t in tests/test_*.sh; do bash "$t" || echo "FAIL $t"; done`
   and confirm no `FAIL` lines print.
8. Commit.

<!-- Plan / decision note (worker-maintained):
- test_viz.py drift was ALREADY fixed on main (byte-identical; `diff` exits 0
  before any edit — prior commit 1299f93 mirrored it), so step 1 was a
  verified no-op; test_viz.py left untouched.
- DECISION (reversible): `workboard/test_workboard.py` is EXCLUDED from the
  include-list. It has since acquired a sanctioned `.agents/skills/` `Run:`
  docstring run-path adaptation (antigravity commit cf8e2b3 "re-apply .agents
  Run: path"), the same class as the already-excluded
  `list-specs/test_list_specs.py`. Including it would make the gate
  permanently red on a legitimate divergence. The current byte-identical
  subset is exactly 6 files — matching SPEC.md's "6 files" claim — and is
  enumerated (fixed, not globbed) in the gate script.
- AGENTS.md left untouched: its `for t in tests/test_*.sh` Commands loop
  picks up the new script by glob (verified — full loop prints no FAIL).
-->

## Acceptance

- [x] `tests/fixtures/content-parity/claude-side/example.py` and `tests/fixtures/content-parity/antigravity-side/example.py` exist and differ from each other; pointing the gate's fixture-redirect seam at them makes it exit nonzero and name `example.py`
  - Evidence: `bash tests/test_antigravity_content_parity.sh --fixture` and `CONTENT_PARITY_FIXTURE=1 bash …` both print `example.py` and exit 1; the two fixtures differ (distinct docstrings + return strings).
- [x] `diff .claude/skills/_shared/test_viz.py antigravity/.agents/skills/_shared/test_viz.py` exits 0
  - Evidence: `diff …/_shared/test_viz.py …` → exit 0 (already byte-identical on main; no edit required).
- [x] `bash tests/test_antigravity_content_parity.sh` exits 0 with no output on the real (fixed) tree
  - Evidence: ran it → no output, exit 0.
- [x] `bash tests/test_antigravity_parity.sh` still exits 0 (existence gate unaffected)
  - Evidence: ran it → exit 0 (file untouched).
- [x] `for t in tests/test_*.sh; do bash "$t" || echo "FAIL $t"; done` prints no FAIL lines
  - Evidence: full loop over all 17 `tests/test_*.sh` (incl. the new gate) → no FAIL lines printed.
