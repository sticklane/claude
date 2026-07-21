# Cheap task-status checks: wire existing tools, add referential-integrity failure

Status: open
Breakdown-ready: true

## Problem

A 2026-07-21 transcript survey (`docs/task-tracking-design-research-2026-07.md`,
"Design comparison" section — read that section for full evidence and the
beads/Dolt comparison; not restated here) found this repo's task-status
checks default to full unbounded `Read` calls 2:1 over cheap header-only
reads (278 vs. 136 across ~70 sessions), even though the cheap machinery
already exists: `.claude/skills/drain/drain_frontier.py` already parses
every task header and computes the authoritative ready/blocked frontier
(drain's own `SKILL.md` step 1 already says so), and `specs/status.sh`
already gives a cheap whole-queue status read. The one **concretely
located** ad hoc check that still falls back to a full `Read` is `build`'s
closing-step sibling scan (checking whether a sibling `tasks/*.md` has
`Status: pending`, to decide whether to print a `/drain` nudge) — dispatch
workers themselves never write or re-check queue status (drain owns all
status writes; a worker only reports a verdict), so the general "point
every ad hoc check at the cheap tools" fix is a documentation/discoverability
gap more than a specific-second-site gap: nothing near drain's own step 1
tells a reader that this convention applies to any OTHER header check that
exists today or gets added later.

Separately, `drain_frontier.py` already flags a dangling `Depends on:`
reference as a diagnostic (`unresolved-external-dep`) but never fails the
run on it — confirmed by reading `main()`: the only nonzero exit is a
malformed `Status:` value (`FrontierError`, e.g. an unparseable dependency
token). There is no way today for a human or CI to ask "does this repo
have any dangling task dependencies" and get a pass/fail answer for a
dependency that parses fine but doesn't resolve to a real task.

## Solution

No new parsing, no new file for the ready-work computation — reuse what
already exists and is already trusted by drain's own dispatch loop.

1. Document the existing tools as the required path for ad hoc header
   checks. `.claude/skills/build/SKILL.md`'s closing-step sibling scan is
   updated to use `grep`, not `Read`. `.claude/skills/drain/SKILL.md` gains
   a short doctrine pointer near step 1 stating that ANY header-only check
   — present or future, in drain or elsewhere — uses `specs/status.sh`,
   `grep '^Status:'`/`grep '^Depends on:'`, or `drain_frontier.py`'s own
   JSON, never an unbounded `Read`. `.claude/rules/token-discipline.md`'s
   "Delegation defaults" section gains the same one-line carve-out as the
   repo-wide doctrine home.
2. Add a `--strict` flag to `drain_frontier.py`, invoked over the whole
   `specs/` tree (not a single spec dir — see Requirements for why a
   per-spec invocation would false-positive). It reuses
   `compute_frontier`'s already-computed `diagnostics` list verbatim: when
   any diagnostic has `kind: "unresolved-external-dep"`, `--strict` prints
   each offending task path and dangling reference to stderr and returns a
   nonzero exit, in addition to (not instead of) emitting the same stdout
   JSON as today. Without the flag, behavior is byte-for-byte unchanged.
   No existing parsing/resolution function is modified — only `main()`'s
   exit handling gains a branch.

## Requirements

- **R1**: `.claude/skills/build/SKILL.md`'s closing-step sibling scan (the
  "does a sibling `tasks/*.md` have `Status: pending`" check) is documented
  as `grep -l '^Status: pending' specs/<slug>/tasks/*.md`-style, not a
  `Read` of each sibling file.
- **R2**: `.claude/skills/drain/SKILL.md` gains a short doctrine line near
  step 1 stating the header-only-check convention applies generally (not
  only to step 1's own `drain_frontier.py` invocation): any check of a
  task's header fields elsewhere in drain's procedure, present or future,
  uses `grep`/`status.sh`/`drain_frontier.py`, never an unbounded `Read`.
- **R3**: `.claude/rules/token-discipline.md`'s "Delegation defaults"
  section gains one line stating the same header-only-check carve-out
  (grep or `status.sh`/`drain_frontier.py`, never a full `Read`, for a
  task's header fields alone) as the repo-wide doctrine home R2 points to.
- **R4**: `drain_frontier.py` gains a `--strict` flag. With no
  `unresolved-external-dep` diagnostic present, behavior (exit code,
  stdout JSON) is byte-for-byte identical with and without the flag. When
  one or more such diagnostics are present, `--strict` emits the same
  stdout JSON as today **plus** prints each offending task path and
  dangling reference to stderr, and returns a nonzero exit. `--strict` is
  documented as a whole-tree check (`drain_frontier.py specs/*/ --strict`)
  — invoking it over a single spec dir can false-positive on a legitimate
  forward cross-spec reference whose target spec simply wasn't included in
  that invocation (confirmed via `drain_frontier.py`'s own
  `_resolve_dep`/cross-spec-path docstring); this requirement does not
  wire `--strict` into any per-spec check. **`drain_frontier.py` is
  byte-identical today across all three trees**
  (`.claude/skills/drain/drain_frontier.py` ≡
  `antigravity/.agents/skills/drain/drain_frontier.py` ≡
  `codex/.agents/skills/drain/drain_frontier.py`, confirmed via `diff`) —
  the same verbatim-mirror convention
  `docs/memory/workboard-mirror-verbatim.md` documents for `workboard.py`
  (not itself named there, but the same pattern: port by `cp`, never
  re-implement). The `--strict` addition is written once and copied
  byte-for-byte into all three locations in the same commit, then
  reconfirmed identical with `diff -q`.
- **R5**: Per `.claude/rules/mirror-procedure-discipline.md`, R1's build
  change is mirrored into `antigravity/.agents/workflows/build.md` (the
  real procedural copy — execution stages port to workflows in
  antigravity, per CLAUDE.md; `antigravity/.agents/skills/build/` does not
  exist) and directly into `codex/.agents/skills/build/SKILL.md`
  (confirmed real-content wrapper, not a symlink). R2's drain doctrine
  line is mirrored into `antigravity/.agents/workflows/drain.md` (same
  reasoning — `antigravity/.agents/skills/drain/` holds only bundled
  scripts, no procedural SKILL.md) and into
  `codex/.agents/skills/drain/SKILL.md` (confirmed real content). R4's
  `drain_frontier.py` change is copied verbatim per R4's own mirror clause
  above — this is a `cp`-and-`diff` step, not a paraphrase, unlike R1/R2's
  prose ports. R3's token-discipline.md line: confirm at implementation
  time whether any of the antigravity files already citing
  token-discipline content inline
  (`antigravity/.agents/skills/design/reference.md`, `qa-sweep/SKILL.md`,
  `harness-audit/SKILL.md`) need the new carve-out added to their citation
  — antigravity has no standalone `rules/` directory to mirror into
  directly.
- **R6**: `.claude-plugin/plugin.json`'s `version` is bumped (skill
  behavior changed in drain and build).

## Out of scope

- **A local SQLite claim/index layer.** Ruled out — see
  `docs/task-tracking-design-research-2026-07.md`'s Design comparison
  section for the full reasoning: `drain_frontier.py` already computes the
  authoritative frontier, and `DRAIN-OWNER.md`'s per-spec git-CAS lease
  already prevents the cross-worker claim race this would have solved.
- **Collision-resistant hash-based task IDs.** Ruled out — same doc,
  same section: git's own add/add merge-conflict behavior already forces
  explicit resolution for the actual failure mode observed here.
- **Richer relation types beyond `Depends on`** (blocks/relates-to/
  duplicates/supersedes) — orthogonal to this spec's status-check-cost
  problem; a natural follow-on.
- Adopting beads/Dolt or any external task-tracker binary.
- Any change to `HANDOFF.md`'s format or `resume-handoff`'s behavior — that
  is `specs/structured-handoff-headers/SPEC.md`, a separate spec.
- Any change to `DRAIN-OWNER.md`'s format — already cheap (107–127 bytes).
- Wiring `--strict` into a per-spec or single-spec-dir CI check — see R4;
  it is a whole-`specs/`-tree tool only.

## Acceptance criteria

Fixtures live under a new
`.claude/skills/drain/test-fixtures/frontier-strict/` directory (created
as part of implementation), passed to `drain_frontier.py` as explicit spec
dirs — its existing CLI already takes arbitrary spec-dir arguments
(`spec_dirs, nargs="+"`), so fixtures never need to live under the real
`specs/` tree and never pollute a real dispatch run. The dangling-dependency
fixture uses a dependency that **parses successfully but resolves to
nothing** — e.g. `Depends on: 99` (a bare number with no matching task in
the fixture spec) — not an unparseable token like a bare word, which
`_parse_deps` raises `FrontierError` on (exit 2 regardless of `--strict`)
before ever reaching the `unresolved-external-dep` diagnostic this flag
targets.

- [ ] `grep -n "grep -l.*Status" .claude/skills/build/SKILL.md` returns a
      match at the closing-step sibling-scan location (R1).
- [ ] `grep -n "status.sh" .claude/skills/drain/SKILL.md` returns a match
      near step 1 stating the general header-only-check doctrine (R2) —
      anchored on `status.sh` alone since `drain_frontier` already appears
      pre-existing at the step-1 invocation and is not a safe anchor.
- [ ] `grep -c "header-only\|never a full .Read." .claude/rules/token-discipline.md`
      → 1 or more (R3).
- [ ] Fixture: a spec dir with a task file `Depends on: 99` (no task
      numbered 99 in that fixture spec) — `python3
      .claude/skills/drain/drain_frontier.py <fixture-dir>` (no flag)
      exits 0 with an `unresolved-external-dep` diagnostic present in
      JSON, unchanged from today; `python3
      .claude/skills/drain/drain_frontier.py <fixture-dir> --strict` exits
      nonzero, emits the same stdout JSON, and additionally prints the
      offending path and dangling reference to stderr (R4).
- [ ] Fixture: a spec dir with only valid `Depends on:` references —
      `--strict` exits 0, stdout output identical to the no-flag run (R4
      regression guard).
- [ ] `diff .claude/skills/drain/drain_frontier.py
      antigravity/.agents/skills/drain/drain_frontier.py && diff
      .claude/skills/drain/drain_frontier.py
      codex/.agents/skills/drain/drain_frontier.py` — both exit 0 (byte-
      identical after the `--strict` addition, R4's mirror clause).
- [ ] `bash tests/test_mirror_procedure_coverage.sh` passes (add the new
      R1/R2 phrases to `tests/mirror-procedure-manifest.txt`, pointing at
      `antigravity/.agents/workflows/{build,drain}.md` per R5 — not
      `antigravity/.agents/skills/{build,drain}/`, which don't hold the
      procedural text).
- [ ] `grep -n "grep -l.*Status" codex/.agents/skills/build/SKILL.md` and
      `grep -n "status.sh" codex/.agents/skills/drain/SKILL.md` each
      return a match (R5's direct codex wiring) — both anchored on the
      phrase confirmed absent today (`drain_frontier` already appears
      pre-existing in the drain file and is not a safe anchor).
- [ ] The closing task's own commit modifies `.claude-plugin/plugin.json`'s
      `version` line — checked against that commit's diff
      (`git show <closing-commit> -- .claude-plugin/plugin.json | grep -q
      '^+.*"version"'`), never a pinned before/after literal (a sibling
      spec landing first can bump the same line first) (R6).

## Open questions

(none)

## Parallelization

Tasks 01 (`drain_frontier.py --strict` + three-tree mirror + fixtures) and
02 (prose wiring in build/drain/token-discipline) are disjoint in `Touch`
and share no undecided design — R4's flag behavior and R1–R3's target
phrasing are both fully pinned by this spec's text, so neither task
depends on the other's implementation. Task 03 (mirror into
antigravity/codex, manifest entries, version bump) depends on both, since
it mirrors and version-bumps their landed content.

- Group: 01, 02
