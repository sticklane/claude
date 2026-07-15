# Verification evidence: 01-checker-fixtures-stamps.md

Verdict: PASS (with one scope-creep finding, non-blocking to acceptance criteria)

Base commit for diff checks: 3348d24
Worktree: /Users/sjaconette/claude/.claude/worktrees/agent-aea5fdc017a4d3b3d

## Acceptance criteria (from task file, run verbatim with <fixed-date>=2026-06-01)

1. ✓ `bash .claude/skills/idea/test-fixtures/research-freshness/check-freshness.sh .claude/skills/idea/test-fixtures/research-freshness/fresh --today 2026-06-01`
   Output: `fresh` — matches.

2. ✓ `... stale --today 2026-06-01`
   Output: `stale` — matches.

3. ✓ `... no-stamp --today 2026-06-01`
   Output: `absent` — matches.

4. ✓ `... file-level-stamp --today 2026-06-01`
   Output: `fresh` — matches.

5. ✓ `grep -A3 "## Dispatch authoring: making the choice explicit" docs/guides/model-routing.md | grep -qE "^Verified: [0-9]{4}-[0-9]{2}-[0-9]{2}$"`
   Exit 0 (PASS). Stamp present: `Verified: 2026-07-14`.

6. ✓ `grep -A3 "## Cross-vendor grounding" docs/guides/model-routing.md | grep -qE "^Verified: [0-9]{4}-[0-9]{2}-[0-9]{2}$"`
   Exit 0 (PASS). Stamp present: `Verified: 2026-07-14`.

7. ✓ `bash tests/test_doc_links.sh`
   Output: `pass: 16 fail: 0`, exit 0.

All 7 literal acceptance commands ran and passed as specified.

## Independent sanity checks

### Strict-adjacency (heading-level) vs. intro-tolerant (file-level fallback)

Read `.claude/skills/idea/test-fixtures/research-freshness/check-freshness.sh`'s
`extract_stamps` awk function directly:

- Heading-level loop (`for j = i+1 to n`) skips only blank lines, then takes
  the FIRST non-blank line; if that line is not exactly
  `Verified: YYYY-MM-DD`, it breaks with `hs=""` — i.e. any intro prose
  between a `##` heading and its own stamp defeats heading-level detection
  (strict adjacency), confirmed.
- File-level loop scans every line in `[h1+1, first_h2-1]` for a `Verified:`
  line anywhere in that range — tolerates an intro paragraph between the H1
  and the stamp, confirmed.

Fixture shapes on disk confirm this is actually exercised:

- `fresh/doc.md` and `stale/doc.md`: `Verified:` line is the immediate next
  non-blank line after the `##` heading (heading-level, strict-adjacent).
- `file-level-stamp/doc.md`: H1 → blank → multi-line intro paragraph →
  blank → `Verified: 2026-05-15` → blank → `## A heading relying on the
file-level stamp` (no stamp of its own). This matches the task's required
  shape and matches `docs/guides/large-codebase-context.md`'s real preamble
  shape (H1, intro paragraph, `Verified:` line, then first `##`), confirmed
  by reading both files.

### Stamp scope restricted to the two named headings only

`git diff 3348d24 -- docs/guides/*.md docs/external-playbooks.md | grep -E
'^\+.*Verified:'` returns exactly 2 added lines, both `Verified: 2026-07-14`,
both inside `docs/guides/model-routing.md` (one under `## Dispatch
authoring: making the choice explicit`, one under `## Cross-vendor
grounding`). No other heading in `docs/guides/*.md` or
`docs/external-playbooks.md` gained a stamp. Confirmed via `git diff
3348d24 -- docs/guides/model-routing.md` showing only two `+Verified:
2026-07-14` insertions plus formatting noise (see Scope-creep finding
below).

### tests/test_doc_links.sh

Re-ran independently (criterion 7 above): `pass: 16 fail: 0`, exit 0.

## Append-only task-file check

`git diff 3348d24 --stat -- '*/tasks/*.md'` → empty. No task file under any
spec's `tasks/` dir changed. The task file's Status/checkboxes are
un-ticked as expected per the caller's note (not scored as a failure per
instructions).

## Scope-creep finding

`git diff 3348d24 -- docs/guides/model-routing.md` shows, in addition to the
two intended `Verified:` stamp insertions, an UNRELATED formatting change in
the "DeepSeek (contrast, not a supporting citation)" section: markdown
emphasis markers were converted from asterisks to underscores in three
places (`*size*` → `_size_`, `*selection*` → `_selection_`, etc.). This is
not required by any acceptance criterion, is not part of adding a
`Verified:` stamp, and touches prose outside the two named headings. It is
minor (a markdown-lint-style auto-format, not a content change) but is
scope creep relative to the task's `## Touch` restriction ("Do not add a
`Verified:` stamp to any heading ... other than the one named above" —
implicitly, the task's mandate is stamp-only edits to this file). Flagging
per the verification charter; does not affect any acceptance command's
pass/fail.

## Gates

- `bash tests/test_doc_links.sh` → pass: 16 fail: 0 (also the literal
  criterion 7).
- No repo-wide `scripts/check.sh` run beyond what's covered above (task is
  narrowly scoped to fixture/checker/stamp work; the acceptance section is
  the canonical check set for this task).

## Overall

PASS — all 7 literal acceptance commands pass verbatim, both sanity checks
on the checker's adjacency/fallback logic confirm the stated behavior, and
the stamp-scope restriction holds (only the two named headings). One
non-blocking scope-creep finding (unrelated emphasis-marker reformatting in
model-routing.md) is reported for the record.
