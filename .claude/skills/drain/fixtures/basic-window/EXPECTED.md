# Expected frontier for basic-window

Command:

    python3 .claude/skills/drain/drain_frontier.py \
      .claude/skills/drain/fixtures/basic-window --window 2

## Reasoning

- Task 01 is `done`, so it is neither dispatchable nor blocked.
- Tasks 02, 03, 04 are `pending` with their only dependency (01) `done`, so
  all three are **dispatchable**. Task 05 is `pending` but depends on the
  still-pending 02, so it is **blocked** (`unmet-deps`), never dispatchable.
- Ordering (Priority, then unblocking-power, then lexicographic): all four
  are P1. Task 02 unblocks one still-pending task (05), giving it
  unblocking-power 1; 03 and 04 have power 0. So dispatchable order is
  `02-alpha, 03-beta, 04-gamma`.
- Admissible (empty-window assumption): `- Group: 02, 03, 04` makes all three
  co-admissible, and their Touch sets (`src/alpha.py`, `src/beta.py`,
  `src/gamma.py`) are pairwise disjoint, so the full admitted set is
  `02, 03, 04`. `--window 2` truncates admissible to the first two.

## Expected admissible under `--window 2`

    02-alpha.md, 03-beta.md
