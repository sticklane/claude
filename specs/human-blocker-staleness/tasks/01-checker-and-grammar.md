# Task 01: the probe grammar, the checker, and its fixtures

<!-- Registration fields (Depends on, Budget, Touch, Rigor) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. Status and Priority are frozen authoring-time display only: bd owns their live values. -->

Status: pending
Depends on: none
Priority: P0
Budget: 40 turns
Spec: ../SPEC.md (requirements R1, R2, R4, R5, R6, R8, R10)
Touch: .claude/rules/human-blockers.md, bin/check-human-blockers, tests/test_human_blockers.sh, tests/inventory/07-human-blocker-probes.json, specs/toolkit-core-simplification/surface-inventory/07-human-blocker-probes.json

## Goal

`.claude/rules/human-blockers.md` defines the `Still-blocked:` clause and its
three-value exit contract, and `bin/check-human-blockers` parses a `HUMAN.md`,
resolves and runs each probe under the R2 grammar, and reports five buckets
with the R5 exit codes. A fixture-driven suite proves the security properties
by observation rather than assertion, and both inventories are registered so
`scripts/check.sh` stays green when this lands.

## Touch

This task writes the mechanism only. It must NOT create
`scripts/blocker-probes/` or edit `HUMAN.md` — real probes and the migration
are task 02's, and the fixture probes this task needs live inside the test's
own temp fixtures, never in the repository's probe directory. It must NOT edit
`.claude/skills/drain/SKILL.md`; that is task 03's.

## Steps

1. Extend `.claude/rules/human-blockers.md`: the mandatory `Still-blocked:`
   clause as the final line element, the three-value contract (0 blocked,
   3 cannot determine, other nonzero stale), the last-` — Still-blocked: `
   parse rule, `none — <reason>` as the only escape, and the sanctioned-rewrite
   exception with its retroactivity note. Keep edits inside the rule's existing
   structure; do not restyle the file.
2. Write the failing test first. `tests/test_human_blockers.sh` builds throwaway
   fixture repositories under `mktemp -d` — following the fixture style already
   in `tests/test_check_inventory.sh` — each with its own `HUMAN.md`, a
   `scripts/blocker-probes/` directory, and a git root, so nothing touches this
   repository.
3. Cover every R8 case: probe exiting 0; exiting nonzero; exiting 3; missing
   clause; `none — <reason>`; hanging past `HUMAN_BLOCKER_PROBE_TIMEOUT=1`;
   a `- [x]` entry with no clause; an unbalanced quote; an absent sibling path
   returning 3; and the four hostile clauses. Three hostile cases die at name
   resolution (`bd list; touch SENTINEL`, `git -c alias.p=!touch\ SENTINEL p`,
   `../../../bin/evil`); the fourth hands a *real* fixture probe a planted
   directory whose `.git/config` sets `core.fsmonitor`, which is the only case
   that reaches the argument grammar.
4. Every case additionally asserts the fixture `HUMAN.md`'s sha256 is unchanged
   and the fixture directory gained no files — the only observation that can
   distinguish a reporting checker from a rewriting one (R6).
5. Implement `bin/check-human-blockers [path]`. Validate the whole clause before
   executing anything: name against `^[a-z0-9][a-z0-9-]*$` with `none`
   reserved, resolution to `<git-root>/scripts/blocker-probes/<name>` as a
   regular executable file, `shlex.split(posix=True)` for arguments, no ASCII
   control characters. Execute as argv with `cwd` at that git root, never
   through a shell.
6. Register the new test: a `tests/inventory/07-human-blocker-probes.json`
   fragment with `"runner": "bash"` and `"disposition": "repair"`, and a
   matching surface fragment with `git_blob_pin: 1`, a `frozen_sha256` over the
   canonical object without that field, and a
   `tests/test_human_blockers.sh#assert:<sha256>` behavioral pointer. `repair`,
   not `retain` — freezing this test on the day it lands re-creates the
   deadlock the spec documents.

## Acceptance

- [x] `bash tests/test_human_blockers.sh` → exits 0, reports 0 failures. **L2**
      — `passed: 21, failed: 0`, exit 0.
- [x] `bash tests/test_human_blockers.sh 2>&1 | grep -c 'SENTINEL'` → ≥ 4
      (one assertion per hostile case; the suite asserts sentinel absence, so
      a case that silently stopped running would drop the count). **L2**
      — 6.
- [x] `python3 scripts/inventory-core-surface.py --root . --check specs/toolkit-core-simplification/BASELINE.json 2>&1 | grep -c 'unclassified\|drift'` → 0. **L2**
      — 0; the run prints `135 classified surfaces`.
- [x] `bash tests/test_check_manual_inventory.sh` → prints `CHECK MANUAL INVENTORY OK`. **L2**
      — printed.
- [ ] `python3 -c "import json;d=json.load(open('tests/inventory/07-human-blocker-probes.json'));print(all(t['disposition']=='repair' for t in d['tests']))"` → `True`. **L1**
      — **NOT MET, deferred.** `scripts/check.sh`'s test-inventory validator
      accepts only `retain`, `quarantine`, or `manual`; a `repair` row fails
      the gate with `tests[0].disposition must be retain, quarantine, or
      manual`, which would turn the whole check red. The row is `retain` and
      the surface fragment carries `repair` — see `## Decisions`.
- [x] `awk '/^## Entry grammar/,/^## Rules/' .claude/rules/human-blockers.md | grep -c 'Still-blocked'` → ≥ 2
      — 4.
      (verified 0 in the whole file today, 2026-07-29; anchored to the grammar
      section rather than a file-wide literal). **L0** — Depth ceiling: prose
      cannot be executed; its behavioral complement is the missing-clause and
      unbalanced-quote fixtures above, which prove the grammar is enforced
      rather than merely written.
- [ ] `bash scripts/check.sh` → `check.sh: green`. **L2** — not run here:
      drain runs the canonical gate once after the review barrier. The
      gate's own inventory validator was run against the real
      `tests/inventory/` and returned 0, scheduling
      `tests/test_human_blockers.sh|bash|retain`.

## Decisions

- `tests/inventory/07-human-blocker-probes.json` disposition: the task and
  R10 ask for `repair`, but `scripts/check.sh` accepts only `retain`,
  `quarantine`, or `manual` in the **test** inventory — `repair` exists only
  in the **surface** inventory's vocabulary. Default taken: `retain` in
  `tests/inventory/`, `repair` in the surface fragment. This preserves the
  intent, because only the surface inventory's `retain` freezes a
  content hash (the deadlock R10 names); the test inventory's `retain` just
  means "run it". Reverse by teaching `scripts/check.sh` a `repair`
  disposition (a separate task, out of this one's `Touch`) and flipping the
  row, or by amending R10 to drop `repair` from the test inventory.
