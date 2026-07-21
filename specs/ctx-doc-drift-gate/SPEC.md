# ctx docs↔binary drift gate: capability claims tested against the CLI

Serves CUJ: all (docs/guides/ctx-cujs.md) — the docs are the adoption
surface; drift converts first contact into a failed call.

Breakdown-ready: true

## Problem

The 2026-07-21 cross-chat review
(../ctx-dispatch-adoption/evidence/ctx-usage-review-2026-07-21.md) found
docs↔binary drift in BOTH directions, with no mechanical check:

1. **Documented-but-absent.** The rollout session's first-ever ctx query
   failed: `ctx map --limit 5` → `error: unexpected argument '--limit'`
   (the binary's flag is `--tokens`). The skill's command table documents
   `map [--limit N]`. That single typo is owned by
   specs/ctx-cujs/tasks/02; this spec owns the CLASS.
2. **Present-but-undocumented (under-claiming).** The skill's scope
   caution says extractors cover "NOT rust", but `ctx tree
   context-tree/src` returns full Rust symbol outlines (live,
   2026-07-21) — the caution steers agents away from a working
   capability, and ctx's own crate is exactly where its spec drains
   grepped instead. Likewise `tree --depth/--limit/--doc`,
   `refs --limit`, `map --doc`, and the global `--no-sync` exist
   undocumented; the fooszone survey hand-rolled `awk '/^tests/'`
   pipelines and parallel `find` runs to approximate output shaping the
   flags partly provide.

Docs here = the ctx SKILL.md (+ antigravity mirror) and
docs/guides/ctx-cujs.md — the two surfaces agents load at query time.

## Requirements

- R1 — Conformance gate. A test in `context-tree/` (cargo test or a
  script test wired into the crate's test run) extracts every
  backtick-quoted `ctx <subcommand> [--flag …]` invocation from
  `.claude/skills/ctx/SKILL.md`, `antigravity/.agents/skills/ctx/SKILL.md`,
  and `docs/guides/ctx-cujs.md`, and asserts each named subcommand and
  each `--flag` exists in the binary's clap definition (parse `ctx
  <sub> --help` or use clap introspection). Unknown subcommand or flag
  fails the test. A regression fixture pins the `map --limit` shape as
  caught. **Waiver list:** the test carries an explicit, commented
  known-drift allowlist seeded with exactly the `map [--limit N]` table
  entry, so R1 can land before specs/ctx-cujs/tasks/02 (which is parked
  at the tail of the SKILL.md editor registry); that task's landing
  empties the waiver list. Acceptance: test exists and runs green; with
  the waiver entry removed and cujs/02 unlanded it fails on the map row
  (demonstrated once in the task's evidence, then re-waived).

- R2 — Stale-claims sweep (SKILL.md edit — registry slot required).
  Correct the capability claims verified stale as of this review: the
  rust scope-caution line (rust is extracted; keep any genuinely
  unextracted languages listed accurately from the extractor registry),
  and document the existing output-shaping flags — `tree
  --depth/--limit/--doc`, `refs --limit`, `map --tokens/--doc`, global
  `--json`/`--no-sync` — as a compact flags note or table column.
  Acceptance: `grep -q 'depth' .claude/skills/ctx/SKILL.md` succeeds
  (confirmed absent from the skill today); the rust caution no longer
  claims rust is unextracted AND `ctx tree context-tree/src` returning
  symbols is cited as the check; skill + antigravity mirror edited in
  the same commit; plugin.json bump per conventions.

- R3 — Reverse-coverage report (non-gating). The R1 test additionally
  emits (never fails on) the list of binary subcommands/flags absent
  from all three doc surfaces, so future under-claiming is visible in
  test output. Acceptance: report emission demonstrated in the task's
  evidence output.

## Landing order

R2 edits the ctx SKILL.md, which is governed by the editor registry in
specs/ctx-skill-token-doctrine ("a spec that edits the skill without a
slot here may not be broken down"). Breakdown of this spec must FIRST
append a slot for R2 to that registry — inserted before the terminal
ctx-cujs R3 slot, which stays last — and R2's task then lands serialized
per the registry. R1 and R3 touch no skill file and may proceed
independently of the registry chain.

## Non-goals

- Fixing the `map --limit` typo itself (specs/ctx-cujs/tasks/02 owns it;
  R1's waiver list exists precisely to respect that ownership).
- Generating the SKILL.md from clap definitions (attractive later; the
  gate is the minimal durable fix).
- Auditing prose claims beyond invocation syntax and the named
  capability cautions (semantic doc review stays human/critic work).

## Evidence

../ctx-dispatch-adoption/evidence/ctx-usage-review-2026-07-21.md
(rollout failure verbatim; live rust-indexing and flag checks
2026-07-21).

Next stage: /critique (this SPEC.md), then /breakdown.
