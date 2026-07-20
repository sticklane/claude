Status: in-progress
Discovered-from: specs/criterion-depth-ladder/tasks/01-doctrine-depth-ladder.md
Spec: ../SPEC.md
Priority: P3
Promotion-ready: true
Promoted-by-run: afeb2e0118315ce0
Budget: 3 turns
Touch: docs/memory.md

# Refresh docs/memory.md index line for anchored-acceptance-criteria

docs/memory.md index line for this doc (line 16) still summarizes only the three original traps (vacuous-grep / unsatisfiable-bound / sibling-bump) and omits the new fourth pattern and depth ladder — a one-line index refresh would keep the summary current.

## Acceptance

- [ ] `grep -c "depth ladder" docs/memory.md` returns non-zero (confirmed 0
      today, 2026-07-20) — the index line names the new "Criterion depth
      ladder" section (L0-L3 levels + deepest-feasible rule) added to
      `docs/memory/anchored-acceptance-criteria.md` this run.
- [ ] `grep -c "deepest-feasible" docs/memory.md` returns non-zero
      (confirmed 0 today) — the deepest-feasible rule is named, not just
      the phrase "depth ladder" in isolation.
- [ ] The edit stays a single-line change to line 16 (`git diff --numstat
    docs/memory.md` shows exactly 1 file, 1 line changed) — the existing
      summary (vacuous-grep / unsatisfiable-bound / sibling-bump) is
      extended, not replaced (line 420 chars today; growing it by one
      clause is expected and fine, no upper bound).

## Original report

Refresh docs/memory.md index line for anchored-acceptance-criteria

docs/memory.md index line for this doc (line 16) still summarizes only the three original traps (vacuous-grep / unsatisfiable-bound / sibling-bump) and omits the new fourth pattern and depth ladder — a one-line index refresh would keep the summary current.
