# Task 01: NOW.md, the focus selector, and dependency-closure scope

<!-- Registration fields (Depends on, Budget, Touch, Rigor) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. Status and Priority are frozen authoring-time display only: bd owns their live values. -->

Status: pending
Depends on: none
Priority: P0
Budget: 40 turns
Spec: ../SPEC.md (requirements EP0, EP17)
Touch: .claude/skills/drain/SKILL.md, specs/NOW.md, bin/now-focus, .claude-plugin/plugin.json, .codex-plugin/plugin.json, specs/toolkit-core-simplification/surface-inventory/drain-economy-01.json, tests/test_drain_focus_selector.sh, tests/inventory/drain-economy-01.json, evals/drain/03-focus-select/setup.sh, evals/drain/03-focus-select/prompt.txt, evals/drain/03-focus-select/assert.sh, evals/drain/03-focus-select/allowed-tools.txt, evals/drain/03-focus-select/skill-deps.txt, evals/drain/03-focus-select/timeout-seconds.txt

## Goal

`specs/NOW.md` exists as the human-owned focus list, and `/drain`'s SKILL.md
selects its focus from that file: bare `/drain` focus-drains the top NOW.md
entry with ready work, `/drain specs/<slug>` names one explicitly, `/drain
--all` preserves and announces today's whole-queue behavior, and an empty
NOW.md stops with a stated message instead of an invented focus. The focus's
scope is its open beads plus the transitive closure of their blocking
dependencies wherever those live, recomputed at every frontier read, with
imported deps attributed to their donor spec. This task also registers the
surface-inventory fragment covering every existing file this spec's tasks
edit, so later tasks' `/breakdown` pre-flight passes.

## Touch

This task owns the *selection* half of drain's loop. It must NOT write the
spillover or chores behavior (task 02), the filing/triage economy (task 03),
the run bead or narration (task 04), or the completion ceremony (task 12) —
all four edit the same SKILL.md and are serialized behind this task for that
reason. `specs/QUEUE.md` is untouched here: its historical-banner role is
unchanged and task 12 owns the one append.

The inventory fragment this task writes covers every *existing* path this
spec's tasks edit — `.claude/skills/drain/reference.md`, `agentic/ready.py`,
`agentic/audit.py`, `bin/janitor`, `.claude/skills/workboard/workboard.py`,
`.claude/skills/workboard/reference.md`,
`.claude/skills/workboard/test_workboard.py`, and `specs/QUEUE.md` — plus this
task's own new files. Later tasks classify only the new files they create, each
into its own numbered fragment (`drain-economy-NN.json`), so no two tasks ever
write the same registry file.

## Steps

1. Write the surface fragment
   `specs/toolkit-core-simplification/surface-inventory/drain-economy-01.json`
   first, following `codebase-memory-hard-cutover.json`'s shape
   (`schema_version: 2`, `git_blob_pin: 1`, a `frozen_sha256` over the
   canonical object without that field). Classify each existing path
   `measure-before-decision` unless it already carries a behavioral test, in
   which case `repair`; never `retain` — freezing a surface this spec is
   about to edit re-creates the deadlock the inventory README documents.
   Confirm with `python3 scripts/inventory-core-surface.py --root . --check`
   before moving on.
2. Write the failing test first: `tests/test_drain_focus_selector.sh` builds
   throwaway repos under `mktemp -d` (fixture style from
   `tests/test_check_inventory.sh`) with their own `specs/NOW.md`, and
   asserts the *parsing* contract a script can own — NOW.md's grammar (one
   slug per line, optional one-line why, comments and blanks ignored), the
   selection order it yields, and the empty-file case. Keep the assertions on
   observable text, never on internals.
3. Create `specs/NOW.md` with a short human-owned header stating that only a
   human edits it, that order is priority, and that WIP is 1. Seed it with
   the current focus or leave the list empty — an empty list is a legal state
   this task must handle, not a bug.
4. Edit `.claude/skills/drain/SKILL.md`'s launch section: the three launch
   forms, the `--all` announcement at launch, the empty-NOW.md stop message
   naming both escapes (`--all` or an explicit slug), and the statement that
   drain never invents a focus.
5. Edit the ready-queue step (step 1 of the loop) so the frontier read is
   scoped: the focus spec's open beads ∪ the transitive closure of their
   blocking dependencies, recomputed on every read, with imported work
   reported under "imported blocking work (from `<slug>`)" and the donor spec
   never marked in-progress for burnup.
6. Keep SKILL.md well under the 500-line authoring budget — push any detail
   longer than a few lines into `.claude/skills/drain/reference.md`'s
   existing structure rather than growing the body.
7. Author the `evals/drain/03-focus-select/` scenario as the behavioral
   complement: a fixture repo with a two-slug NOW.md, ready work under both,
   and assertions that the run claims only slug[0]'s closure. Do not run it —
   see Acceptance.
8. Register the new test in `tests/inventory/drain-economy-01.json` with
   `"runner": "bash"`, matching the disposition vocabulary `scripts/check.sh`
   accepts (`retain`, `quarantine`, or `manual` — `repair` exists only in the
   surface inventory).

## Acceptance

- [ ] `bash tests/test_drain_focus_selector.sh` → exits 0, reports 0
      failures. **L2**
- [ ] `python3 scripts/inventory-core-surface.py --root . --check specs/toolkit-core-simplification/BASELINE.json 2>&1 | grep -c 'unclassified\|drift'` → 0. **L2**
- [ ] `python3 .claude/skills/breakdown/preflight-acceptance-inventory.py --baseline specs/toolkit-core-simplification/BASELINE.json --path .claude/skills/drain/reference.md --path agentic/ready.py --path agentic/audit.py --path bin/janitor --path .claude/skills/workboard/workboard.py --path .claude/skills/workboard/reference.md --path .claude/skills/workboard/test_workboard.py --path specs/QUEUE.md` → `preflight: PASS`, exit 0. **L2**
- [ ] `awk '/^## The loop/{f=1} f&&/^## Auto-breakdown/{exit} f' .claude/skills/drain/SKILL.md | grep -c 'focus-drain'` → ≥ 1
      (verified 0 in the whole file today, 2026-07-30; anchored to the loop
      section rather than a file-wide literal). **L0** — Depth ceiling: skill
      prose is not executable; the behavioral complement is the
      `evals/drain/03-focus-select` scenario below.
- [ ] `grep -c -- '--all' .claude/skills/drain/SKILL.md` → ≥ 1, and
      `grep -c 'NOW.md' .claude/skills/drain/SKILL.md` → ≥ 2 (both verified 0
      today, 2026-07-30). **L0** — Depth ceiling: as above.
- [ ] `test -f specs/NOW.md && head -1 specs/NOW.md | grep -c .` → 1. **L1**
- [ ] `wc -l < .claude/skills/drain/SKILL.md` → < 500, the SKILL.md size
      budget in the repository's authoring conventions. **L1**
- [ ] `ls evals/drain/03-focus-select/ | wc -l` → 6 (the file set every
      scenario carries), and `grep -c 'NOW.md' evals/drain/03-focus-select/setup.sh`
      → ≥ 1. **L1**
- [ ] `bash evals/run.sh drain` → the new scenario passes. **L3** —
      `manual-pending`: every scenario is a paid headless session against a
      live CLI, and an unattended worker must not launch a paid
      nondeterministic eval (`docs/memory/unattended-worker-tool-limits.md`).
      A human runs this and records the result on this task.
- [ ] `bash scripts/check.sh` → `check.sh: green`. **L2**
