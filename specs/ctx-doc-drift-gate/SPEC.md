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
  each `--flag` exists in the binary's clap definition (parse `--help`
  output or use clap introspection). Unknown subcommand or flag fails
  the test. Tokenizer contract (the docs already contain these shapes —
  a single-level parser falsely rejects valid rows): the extractor
  resolves NESTED subcommands by recursing (`ctx notes list --help`,
  `ctx notes add --help` — `--file` and `--kind` live on the nested
  commands, not on `notes`, verified against the binary), distinguishes
  subcommand tokens from positional placeholders, and strips
  placeholder syntax while still validating flags inside it: `<...>`
  placeholders, `[...]` optional groups (flags inside them ARE
  validated — the `map [--limit N]` catch depends on this), quoted
  string args, `a|b|c` enum values, and the `at <file>:<line>` colon
  form. A regression fixture pins the `map --limit` shape as caught.
  **Waiver list:** the test carries an explicit, commented known-drift
  allowlist keyed by INVOCATION SHAPE (subcommand + flag), matching
  across all three doc files — one seeded entry, `map --limit`, covers
  both the skill's and the antigravity mirror's identical row — so R1
  can land before specs/ctx-cujs/tasks/02 (parked at the registry
  tail). A waiver entry that no longer matches any doc row is reported
  as a WARNING in R3's report section, never a failure (a stale-waiver
  hard-fail would leave main red between cujs/02 landing and cleanup).
  Waiver retirement is owned by THIS spec: a dedicated task, blocked on
  cujs/02 landing, whose Touch includes the R1 test file, deletes the
  seeded entry — cujs/02's own Touch has no grant to the test file, so
  it cannot do it. The retirement task's own acceptance is "the R1
  test runs green with the seeded entry removed" — running it before
  cujs/02 lands fails on the map row, so premature execution
  self-detects rather than silently redding main. Acceptance: test exists and runs green; with the
  waiver entry removed and cujs/02 unlanded it fails on the map row in
  BOTH files (demonstrated once in the task's evidence, then
  re-waived); the stale-waiver warning path has a test.

- R2 — Stale-claims sweep (SKILL.md edit — registry slot required).
  Correct the capability claims verified stale as of this review: the
  rust scope-caution line (rust is extracted; keep any genuinely
  unextracted languages listed accurately from the extractor registry),
  and document the existing output-shaping flags — `tree
  --depth/--limit/--doc`, `refs --limit`, `map --tokens/--doc`, global
  `--json`/`--no-sync` — under a section headed exactly
  `## Output-shaping flags` (a FIXED anchor, since `--json` and
  `--limit` already appear scattered in the current skill body and must
  not vacuously satisfy this). Acceptance: for each of the six flag
  literals `--depth`, `--limit`, `--doc`, `--tokens`, `--json`,
  `--no-sync`: `sed -n '/^## Output-shaping flags/,/^## /p'
  .claude/skills/ctx/SKILL.md | grep -c -- '<flag>'` ≥1 — the sed
  scoping makes the check runnable and immune to pre-existing scattered
  mentions (`--depth`, `--tokens`, `--doc`, `--no-sync` are confirmed
  absent from the whole skill today; the section header is confirmed
  absent too); the rust caution fix is runnable —
  `grep -c 'NOT rust' .claude/skills/ctx/SKILL.md` = 0 (the literal
  exists in the scope cautions today) AND `grep -q 'ctx tree
  context-tree/src' .claude/skills/ctx/SKILL.md` succeeds (the cited
  self-check, confirmed absent today);
  skill + antigravity mirror edited in the same commit; plugin.json
  bump per conventions. R1's conformance test then validates every
  newly documented flag against the binary, closing the loop.

- R3 — Reverse-coverage report (non-gating). The R1 test additionally
  emits (never fails on) the list of binary subcommands/flags absent
  from all three doc surfaces, so future under-claiming is visible in
  test output. Acceptance: the test asserts the report section itself
  is emitted (present and well-formed even when empty), so an
  unattended worker has a runnable check; the populated output is
  additionally captured once in the task's evidence.

## Landing order

R2 edits the ctx SKILL.md, which is governed by the editor registry in
specs/ctx-skill-token-doctrine ("a spec that edits the skill without a
slot here may not be broken down"). The BREAKDOWN SESSION (not a
dispatched worker) must FIRST, in one commit: (a) insert R2's slot into
that registry immediately before the terminal ctx-cujs slot, which
stays last; (b) increment the registry's opening "SEVEN specs" count to
the new total; (c) amend specs/ctx-cujs/tasks/02 to stay internally
consistent — EVERY 7-slot assumption in that file, enumerated: the
landed-gate marker list gains R2's marker; the "If ANY of the 6
markers" gate count increments; the "tail of a 7-spec SKILL.md
serialization chain" count, the "SIX OTHER specs" enumerated list
(adding ctx-doc-drift-gate), and the `all 6 slots landed` echo string
update; the frozen "SLOT 7" number and the
`SPEC.md:20`/`SPEC.md:5-24` line citations re-anchor to the inserted
registry text. cujs task 02's gate greps exactly its listed predecessor
markers, so without (c) "cujs lands last" is unenforced against R2 (R2
and cujs/02 both edit the command-table region, so this serialization
is load-bearing, not cosmetic). Before touching the registry, the
breakdown session checks specs/ctx-cujs/DRAIN-OWNER.md for a live
drain lease; a live lease defers the ENTIRE registry commit — (a), (b),
and (c) together, atomically — never a split that lands (a)+(b) while
deferring (c), which would leave the registry at N slots while cujs/02
still greps N-2 markers, exactly the inconsistency (c) prevents
(concurrent-sessions rule; cujs/02 is parked DEFERRED, so a short wait
is cheap — the R2 task is simply filed blocked on the registry commit).
R2's task then lands
serialized per the registry. R1 and R3 touch no skill file and may
proceed independently of the registry chain — but note R1 depends on
nothing landing first thanks to its waiver list. If
specs/ctx-output-shape-gaps is broken down in the same pass, its R3
slot follows the same mechanics; whichever breakdown runs second
increments the already-updated count.

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

## Parallelization

No concurrent-safe groups. Task 01 runs solo; tasks 02 and 03 are filed
blocked (02 on the deferred registry commit — live ctx-cujs drain lease
at breakdown time, 2026-07-21; 03 on ctx-cujs/tasks/02 landing) and are
serial behind their unblocks by construction.
