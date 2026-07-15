# Task 01: check-freshness.sh, its test fixtures, and the R1 dogfood stamps

Status: done
Depends on: none
Priority: P0
Budget: 10 turns
Spec: ../SPEC.md (requirements R1, R3)
Touch: .claude/skills/idea/test-fixtures/research-freshness/, docs/guides/model-routing.md

## Goal

`.claude/skills/idea/test-fixtures/research-freshness/check-freshness.sh
<dir> [--today YYYY-MM-DD]` scans a `docs/`-shaped tree for `##` headings,
checks each for a `Verified: YYYY-MM-DD` line (heading-level, falling back
to a file-level H1 stamp when the heading has none of its own — a
heading-level stamp always wins when both exist), and prints one of
`fresh` / `stale` / `absent` per matching heading (fresh = within 90 days
of `--today`, stale = older, absent = no stamp at either level). Four
fixture trees exist under the same directory: `fresh/`, `stale/`,
`no-stamp/`, `file-level-stamp/` — each fixture's `Verified:` date is
computed relative to `--today`, never hardcoded. Separately,
`docs/guides/model-routing.md`'s `## Dispatch authoring: making the
choice explicit` heading gets a real current-dated `Verified:` stamp (its
body cites the Anthropic URLs verified this session). The sibling spec
`specs/archive/model-routing-multi-vendor-citations` has already shipped
— `docs/guides/model-routing.md`'s own `## Cross-vendor grounding`
heading (line ~71) exists today with no stamp yet, so it also gets a
current-dated `Verified:` stamp in this same task (confirmed present,
confirmed unstamped, at authoring time — re-check both facts fresh since
this repo's specs churn fast).

## Touch

Do not touch `.claude/skills/idea/SKILL.md` or
`antigravity/.agents/skills/idea/SKILL.md` — those belong to tasks 02 and 03. Do not add a `Verified:` stamp to any heading in
`docs/external-playbooks.md` or `docs/guides/*.md` other than the one
named above — R1 deliberately narrows the dogfood scope to only the
heading actually re-verified this session; every other externally-cited
heading stays unstamped (reads as "stale" per R3, which is the honest
state for unverified content).

## Steps

1. Write failing tests first (a small test harness or just the four
   fixture-driven acceptance checks below, run manually) for the
   fresh/stale/absent/file-level-stamp scenarios.
2. Implement `check-freshness.sh`: parse `--today` (default: real current
   date), walk the target directory's markdown files, find each `##`
   heading, look for a `Verified: \d{4}-\d{2}-\d{2}` line as the next
   non-blank line below it (exact format, no other text on that line,
   strict adjacency — no intro prose permitted between a `##` heading and
   its own stamp); if absent, fall back to a file-level stamp: a
   `Verified:` line appearing ANYWHERE in the file's preamble (after the
   H1, before the first `##`) — this fallback tolerates an intro
   paragraph between the H1 and the stamp, unlike the strict
   heading-level case. Classify fresh/stale (90-day window)/absent per
   heading.
3. Create the four fixture trees under
   `.claude/skills/idea/test-fixtures/research-freshness/`: `fresh/` (a
   heading-level stamp, strictly adjacent, within 90 days of a fixed
   `--today`), `stale/` (a heading-level stamp 100+ days before),
   `no-stamp/` (a heading with neither a heading- nor file-level stamp),
   `file-level-stamp/` (a heading with NO stamp of its own, whose file's
   preamble carries a stamp within 90 days of `--today` — **the preamble
   must include an intro paragraph between the H1 and the stamp**,
   matching `docs/guides/large-codebase-context.md`'s actual shape
   exactly: H1, blank line, multi-line intro paragraph, blank line,
   `Verified:` line, blank line, first `##` heading — a fixture with the
   stamp immediately after the H1 would pass a stricter checker
   implementation than the real file needs and wouldn't prove the
   fallback actually works on it).
4. Add the `Verified: <today>` stamp to both
   `docs/guides/model-routing.md`'s `## Dispatch authoring: making the
choice explicit` heading and its `## Cross-vendor grounding` heading.

## Acceptance

Verified by independent verifier (fixed-date `2026-06-01`); full report:
../evidence/01-checker-fixtures-stamps.md

- [x] `bash .claude/skills/idea/test-fixtures/research-freshness/check-freshness.sh .claude/skills/idea/test-fixtures/research-freshness/fresh --today <fixed-date>` prints `fresh` — verifier: prints `fresh`
- [x] `bash .claude/skills/idea/test-fixtures/research-freshness/check-freshness.sh .claude/skills/idea/test-fixtures/research-freshness/stale --today <fixed-date>` prints `stale` — verifier: prints `stale`
- [x] `bash .claude/skills/idea/test-fixtures/research-freshness/check-freshness.sh .claude/skills/idea/test-fixtures/research-freshness/no-stamp --today <fixed-date>` prints `absent` — verifier: prints `absent`
- [x] `bash .claude/skills/idea/test-fixtures/research-freshness/check-freshness.sh .claude/skills/idea/test-fixtures/research-freshness/file-level-stamp --today <fixed-date>` prints `fresh` — verifier: prints `fresh`
- [x] `grep -A3 "## Dispatch authoring: making the choice explicit" docs/guides/model-routing.md | grep -qE "^Verified: [0-9]{4}-[0-9]{2}-[0-9]{2}$"` (`-A3`,
      not `-A1` — the stamp must be the next NON-BLANK line per the
      heading-level rule, but a literal blank line between the heading
      and the stamp is normal markdown and shouldn't fail this check) — verifier: exit 0
- [x] `grep -A3 "## Cross-vendor grounding" docs/guides/model-routing.md | grep -qE "^Verified: [0-9]{4}-[0-9]{2}-[0-9]{2}$"` — verifier: exit 0
- [x] `bash tests/test_doc_links.sh` still passes after the stamp additions — verifier: `pass: 16 fail: 0`

## Decisions

- Fixed `--today` for the acceptance/test harness = `2026-06-01`; fixture stamps set as deliberate offsets (fresh/file-level = 2026-05-15, stale = 2026-01-01). Reverse: pick a different fixed date and adjust the four fixture stamps accordingly.
- Reverted an unrelated prettier auto-format (asterisk→underscore emphasis in model-routing.md's DeepSeek section) that the Edit-hook introduced, keeping the file diff stamp-only per the task's Touch mandate. Reverse: re-run prettier on the file to restore underscore emphasis.
