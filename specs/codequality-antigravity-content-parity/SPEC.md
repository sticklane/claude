# Antigravity content parity: gate mirrored-file content, not just existence

Status: open
Breakdown-ready: true

## Problem

CLAUDE.md's mirror contract ("When a skill changes here, mirror the change
there in the same commit") has no content-level enforcement. The existing
gate, `tests/test_antigravity_parity.sh`, is existence-only **by its own
spec** (header lines 18–21: "this gate never inspects a mirrored skill's
content (R5)") — it proves every `.claude/skills/*` name has a mirror
directory, workflow file, or README exemption, and nothing more.

Real drift has already shipped undetected:
`.claude/skills/_shared/test_viz.py` carries
`test_viz_axis_labels_carry_muted_tint_with_token_fallback` (asserting the
`var(--viz-muted, #898781)` token fallback in `viz.VIZ_CSS`) that
`antigravity/.agents/skills/_shared/test_viz.py` lacks — verified 2026-07-10
via `diff` (lines 199–210 present only on the `.claude` side). `viz.py`
itself is byte-identical on both sides, so this is pure coverage drift the
mirror would pass if it had the test.

Byte-parity is NOT the de-facto contract for every mirrored `.py` file: of
the 10 mirrored `.claude/skills/*.py` / `antigravity/.agents/skills/*.py`
pairs, 4 currently differ, and 3 of those are legitimate, sanctioned port
adaptations rather than drift — `prioritize/prioritize_scan.py` (a
standalone-install docstring), `list-specs/test_list_specs.py`, and
`prioritize/test_prioritize_scan.py` (both carry the antigravity
`.agents/skills/` run-path adaptation). Only `_shared/test_viz.py` is real,
unsanctioned drift. Byte-parity holds only for the narrower,
contractually-identical subset — `_shared/*.py`, `workboard/*.py`, and
`list-specs/list_specs.py` (6 files, verified byte-identical today) — so
the gate below scopes to that include-list rather than every `.py` file,
to avoid flagging the sanctioned port adaptations as false positives.

## Approach

1. Fix the current drift: copy the missing test into
   `antigravity/.agents/skills/_shared/test_viz.py` (mirror-only change;
   per CLAUDE.md conventions this still needs a `plugin.json` version bump
   only if skill behavior changes — a test mirror does not, decide in the
   task).
2. Add a content-parity gate, e.g. `tests/test_antigravity_content_parity.sh`,
   that asserts `diff -q` emptiness for a fixed include-list of
   contractually-identical `.py` files — `_shared/*.py`, `workboard/*.py`,
   and `list-specs/list_specs.py` — comparing each `.claude/skills/<path>`
   against `antigravity/.agents/skills/<path>`, printing each divergent path
   on failure. Do NOT glob every mirrored `.py` file: `prioritize/*.py` and
   `list-specs/test_list_specs.py` carry sanctioned port adaptations (see
   Problem) and must stay out of the include-list, or the gate can never go
   green. Keep it separate from `test_antigravity_parity.sh` so the existing
   R1–R5 spec (specs/antigravity-parity-gate) stays untouched; scope it to
   `.py` files first (SKILL.md prose legitimately diverges between runtimes
   — that stays out of scope unless a later task defines a prose-normalization
   rule).
3. Wire it into the AGENTS.md Commands loop (`for t in tests/test_*.sh`)
   — it picks it up automatically by glob; verify.

## Out of scope

- Content parity for SKILL.md prose, agents→skills ports, or hook JSON —
  those diverge by design (antigravity is a *port*, not a copy).
- Changing `test_antigravity_parity.sh` itself.

## Acceptance criteria

- [ ] A committed fixture pair,
      `tests/fixtures/content-parity/claude-side/example.py` and
      `tests/fixtures/content-parity/antigravity-side/example.py`, holds
      two deliberately-divergent files (permanent, order-independent — not
      the pre-fix tree, which the drift fix below removes). Pointing the
      gate's comparison at this fixture pair (e.g. via an env var or
      `--fixture` flag the gate script accepts) exits nonzero and names
      `example.py`, proving the gate catches divergence.
- [ ] `diff .claude/skills/_shared/test_viz.py antigravity/.agents/skills/_shared/test_viz.py`
      exits 0 (drift fixed).
- [ ] `bash tests/test_antigravity_content_parity.sh` exits 0 with no
      output on the fixed tree.
- [ ] `bash tests/test_antigravity_parity.sh` still exits 0 (existence gate
      unaffected).
- [ ] `for t in tests/test_*.sh; do bash "$t" || echo "FAIL $t"; done`
      prints no FAIL lines.
