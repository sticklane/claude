# Antigravity content parity: gate mirrored-file content, not just existence

Status: open

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
mirror would pass if it had the test. Every other mirrored `.py` file is
currently byte-identical, which shows byte-parity is the de-facto contract
for the Python scripts.

## Approach

1. Fix the current drift: copy the missing test into
   `antigravity/.agents/skills/_shared/test_viz.py` (mirror-only change;
   per CLAUDE.md conventions this still needs a `plugin.json` version bump
   only if skill behavior changes — a test mirror does not, decide in the
   task).
2. Add a content-parity gate, e.g. `tests/test_antigravity_content_parity.sh`,
   that for every `.py` file under `.claude/skills/` with a counterpart
   under `antigravity/.agents/skills/` asserts `diff -q` emptiness, printing
   each divergent path on failure. Keep it separate from
   `test_antigravity_parity.sh` so the existing R1–R5 spec
   (specs/antigravity-parity-gate) stays untouched; scope it to `.py` files
   first (SKILL.md prose legitimately diverges between runtimes — that stays
   out of scope unless a later task defines a prose-normalization rule).
3. Wire it into the AGENTS.md Commands loop (`for t in tests/test_*.sh`)
   — it picks it up automatically by glob; verify.

## Out of scope

- Content parity for SKILL.md prose, agents→skills ports, or hook JSON —
  those diverge by design (antigravity is a *port*, not a copy).
- Changing `test_antigravity_parity.sh` itself.

## Acceptance criteria

- [ ] Before the drift fix, `bash tests/test_antigravity_content_parity.sh`
      exits nonzero and names `_shared/test_viz.py` (proves the gate
      catches the known drift — run this on the pre-fix tree or a fixture).
- [ ] `diff .claude/skills/_shared/test_viz.py antigravity/.agents/skills/_shared/test_viz.py`
      exits 0 (drift fixed).
- [ ] `bash tests/test_antigravity_content_parity.sh` exits 0 with no
      output on the fixed tree.
- [ ] `bash tests/test_antigravity_parity.sh` still exits 0 (existence gate
      unaffected).
- [ ] `for t in tests/test_*.sh; do bash "$t" || echo "FAIL $t"; done`
      prints no FAIL lines.
