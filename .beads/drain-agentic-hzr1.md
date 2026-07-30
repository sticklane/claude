Depends on: agentic-zz3k (closed, merged)
Priority: P0
Budget: 30 turns
Touch: bin/janitor, tests/test_janitor_worktree_sweep.sh
Rigor: production

# agentic-hzr1 — janitor's dry run must name what it would destroy

## Goal

`bin/janitor --dry-run` emits one record per candidate worktree — enough for a
human to approve or reject the plan without re-deriving it by hand.

## Why this gates real work

Measured 2026-07-30, immediately after the sweep rules landed:

    janitor summary:
      scope=drain
      dry_run=true
      reclaimed_claims=0
      reclaimed_worktrees=7
      salvaged_worktrees=0
      skipped_or_ambiguous=18

`--json` returns the same counts plus an empty `handoff_scope`, with no
per-item array. So the tool says it would delete seven directories and will
not say which seven.

A dry run exists so a human can approve a destructive plan before it runs. One
that names no targets cannot be approved on its own evidence — the reviewer
must re-derive the plan by hand, which is exactly the work the dry run was
supposed to replace. It also makes the three-way classification unauditable:
nothing shows whether a given worktree was judged clean, reconstructible, or
unique-and-salvaged.

The human has declined to run `--apply` against the live checkout until this
lands. 17 worktrees are waiting on it.

## Scope

Report only. Do NOT change which worktrees janitor selects, or any of the
three safety rules — `agentic-zz3k` just landed those with test coverage, and
a selection change here would be indistinguishable from a reporting change in
review.

Per candidate, emit: path; branch (or detached); owning issue id and its
status; category (clean / reconstructible / unique / detached); the action it
would take (remove / salvage-then-remove / skip); and for a skip, the reason.

Keep the existing summary counts as a trailing summary — they are useful, just
insufficient alone. `--json` carries the per-item array as structured data;
human-readable output carries one line per candidate.

The same records should appear under `--apply`, describing what was done
rather than what would be done, so the ledger and the plan have the same
shape.

## Steps

1. Extend `tests/test_janitor_worktree_sweep.sh` FIRST with assertions on the
   per-candidate output, and confirm they fail against today's janitor.
2. Implement the reporting.
3. Confirm the existing 18 assertions still pass — selection behavior must be
   untouched.

## Acceptance

- [ ] A1 (cheap): `bash tests/test_janitor_worktree_sweep.sh` exits 0 with 0
      failures, and its assertion count is strictly greater than 18 (the count
      `agentic-zz3k` left).
- [ ] A2 (cheap): the test asserts that for a fixture with a known reclaimable
      worktree, `--dry-run` output contains that worktree's path. Assert the
      path itself, not merely that output is non-empty.
- [ ] A3 (cheap): the test asserts each of the four categories (clean,
      reconstructible, unique, detached) is reported by name for a fixture
      exercising it.
- [ ] A4 (cheap): the test asserts `--dry-run --json` parses as valid JSON and
      contains a per-candidate array whose length equals the number of
      candidates, each element carrying path, branch, issue, status, category,
      and action keys.
- [ ] A5 (cheap): the test asserts a SKIPPED candidate reports a reason, and
      that the reason distinguishes at least the live-session skip from the
      shared-checkout skip.
- [ ] A6 (cheap): selection is unchanged — the test asserts the same fixtures
      produce the same removed/kept outcomes as before this task. State in
      your return how you pinned that, rather than asserting it in prose.
- [ ] A7 (cheap): `python3 scripts/inventory-core-surface.py --root . --check specs/toolkit-core-simplification/BASELINE.json`
      exits 0.
- [ ] A8 (cheap): run `bin/janitor --scope drain --dry-run` against THIS real
      repository and paste its output in your return. It must name paths. This
      is the output a human will approve, so it is the real deliverable — if
      it is not reviewable, the task is not done.

## Notes

Do not run `scripts/check.sh`; drain runs the canonical gate once after an
independent review barrier.

If you touch a `surface-inventory/` fragment, write it correct in the SINGLE
commit that introduces it — a fragment is pinned to the blob of the commit
that added it, so amending one later makes the branch permanently ungateable
(bd issue `agentic-1t9d`).

`grep` here wraps ugrep 7.5.0 and omits the leading `./` when recursing `.`,
so `grep -v '^\./…'` exclusions silently match nothing
(docs/memory/anchored-acceptance-criteria.md).
