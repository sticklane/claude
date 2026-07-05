# Unit tests for the pure parsing/layout functions

Status: done
Priority: P2
Source: holistic best-practices review (2026-07-04) — critic finding #1

## Problem

`scripts/check.sh` only runs `py_compile`, one render smoke test, and an `_iso`
assertion. ~1200 lines of intricate, regex-heavy parsing is otherwise untested.
The smoke test asserts only `"Workboard" in html`, so a regex that silently
starts returning `[]` (REPOS.md table format shifts, `Depends on:` phrasing
changes, frontmatter folding breaks) blanks a whole section **while the gate
stays green.** These functions are already pure and side-effect-free, so they're
trivially testable with hand-built fixture strings — no server, no filesystem.

## Scope

Add `tests/test_parsers.py` (stdlib `unittest`, run from `scripts/check.sh`)
covering, at minimum:

- `_parse_frontmatter` — multi-line description folding; missing closing `---`;
  no frontmatter; the `flush()` continuation logic.
- `_parse_task` — `Depends on: 01, 02` vs `none` vs a cross-spec path ref;
  `num` from filename prefix; `Task NN:` title stripping.
- `_status_of` — open/closed/blocked buckets.
- `parse_repos` — the `^\|\s*(~[^|]*?)\s*\|` regex skips the header and `|---|`
  separator rows; tolerates a missing REPOS.md.
- `collect_sessions` state classification — active/recent(<48h)/stale(>7d)/idle
  boundaries; `last==0` → not active.
- `_iso` — epoch-ms int, ISO string, junk.
- `_gh_slug` — https, ssh, `.git` suffix, non-github, None.
- `_dep_graph_svg` — a **cyclic** `deps` input returns without hanging; an
  acyclic one produces the expected node/edge counts.

## Acceptance

- `scripts/check.sh` runs the new tests and they pass; a deliberately broken
  regex makes a test fail (proving the tests bite).
- No network, no filesystem, no server spawned by the tests.

## Out of scope

- Integration tests against the live HTTP server or real `~/.claude` state.
