# ctx: zone-tagged dead/archived trees — keep them indexed, make them legible

Serves CUJ: DEDUP / DEAD CODE, and LOCATE hygiene (docs/guides/ctx-cujs.md).

Breakdown-ready: true

## Problem

Steven directive (2026-07-21): "dead code is good to find actually" —
reversing the earlier framing that treated `attic/` hits as pollution
to exclude. In the fooszone survey, `refs lerp` and `refs rodSpecs`
returning `attic/go-cmd/mloverlay` hits was NOISE when answering "who
uses this live?" but would have been SIGNAL when asking "does a dead
copy of this exist?" or "is this symbol only kept alive by dead code?"
Blanket exclusion (the original plan for attic via `.ctxignore`)
destroys the second use to serve the first. The right shape: dead
trees stay indexed, results are visibly tagged, and filtering is a
per-query choice.

Consequence already applied upstream: fooszone
`specs/repo-orientation-hygiene` R3 is amended (same day) to exclude
only `vendor/` + `dist/`, keeping `attic/` indexed pending this spec.

## Solution

A repo-level zone config maps path globs to zone labels; queries tag
matching result paths and can filter by zone. Zones are orthogonal to
membership (`.ctxignore` removes; zones annotate) and to minified
skipping (specs/ctx-minified-skip).

Config: reuse the `.ctxignore` file's home and matcher grammar in a
sibling file `.ctxzones`, one `<label>: <glob>` per line (e.g.
`archived: attic/`). Line-grammar edges (pinned here so goldens don't
freeze accidents): label charset `[a-z0-9-]+`; the same label may
appear on multiple lines (globs union); when two labels match one
path, first match in file order wins (single tag per path);
`--zone <label>` with an undeclared label errors (exit 2, message
lists declared labels). No new glob syntax. Zero config → zero zones
→ output byte-identical to today.

Seam with specs/ctx-absence-check (one sentence, mirrored there):
"no-match" means SYMBOL RESOLUTION FAILED and triggers the
absence-check boundary output; a symbol that resolves but whose
results are emptied by filters (`--live-only`, `--in`, `--zone`) is
NOT a no-match — it emits R3's zones/filter tail, never the absence
boundary, and exits 0.

## Requirements

- R1 — Zone tagging: `refs`/`tree`/`map` (text and `--json`) annotate
  results whose path matches a zone glob with `[zone:<label>]` (JSON:
  a `zone` field). Golden tests with a fixture `.ctxzones`.
- R2 — Zone filtering: `--zone <label>` (only that zone) and
  `--live-only` (exclude all zones) on `refs` and `map`, composing
  with `--in/--not-in` from specs/ctx-query-ergonomics R3 (that spec's
  filters land first or together — name the ordering in breakdown).
  Golden tests.
- R3 — Dead-only liveness query: `ctx refs <sym> --live-only`
  returning zero refs while plain `refs` returns zone hits is the
  primitive for "only kept alive by dead code". Acceptance: fixture
  where a symbol's every reference is in-zone; `--live-only` output
  is empty with a one-line "N references exist only in zones:
  <labels>" tail and exit 0 (resolution succeeded; contrast plain
  refs no-match which stays nonzero — see the seam definition in
  Solution; never a bare empty result — filtered-out must not look
  like absent). Golden tests name their commands: `ctx refs <sym>`,
  `ctx refs <sym> --live-only`, `ctx refs <sym> --zone archived`,
  each in text and `--json` modes.
- R4 — Docs: skill command table + scope cautions updated (rewrites
  the attic/vendored caution AUTHORED BY token-doctrine R7 — hard
  dependency, R7 must land first — to "zone dead trees, don't exclude
  them"). This holds SLOT 5 of the SKILL.md editor registry in
  token-doctrine's Landing order; skill + antigravity mirror
  same-commit. The CUJ doc's DEDUP/DEAD CODE section
  (specs/ctx-cujs R1) cites this spec.
- R5 — fooszone follow-through: ALREADY RECORDED upstream — fooszone
  `specs/repo-orientation-hygiene/SPEC.md` (REVISED 2026-07-21)
  documents the `.ctxzones` + `archived: attic/` follow-up and its
  TASKS.md line. This requirement is a no-op pointer; no task is
  emitted for it.

## Non-goals

- Automated dead-code DETECTION (deciding what is dead) — zones are
  declared by humans; the detection question belongs to
  specs/ctx-static-analysis-augmentation's tooling tier.
- Cross-zone rename/impact semantics — IMPACT CUJ handles zones like
  any other path.
