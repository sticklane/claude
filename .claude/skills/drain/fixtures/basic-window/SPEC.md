# basic-window (drain_frontier golden fixture)

Status: open

A committed golden fixture for `drain_frontier.py`. It lives under
`.claude/skills/drain/fixtures/` — NEVER under real `specs/`, where drain's
no-arg queue walk and list-specs would treat its pending tasks as live work.
See `EXPECTED.md` for the documented `--window 2` expectation.

## Parallelization

Tasks 02, 03, 04 are Touch-disjoint and share no undecided design.

- Group: 02, 03, 04
