# Task 01: check-freshness.sh, its test fixtures, and the R1 dogfood stamps

Status: pending
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
   non-blank line below it (exact format, no other text on that line); if
   absent, look for the same pattern as the next non-blank line after the
   file's H1 title and treat it as that heading's stamp; classify
   fresh/stale (90-day window)/absent per heading.
3. Create the four fixture trees under
   `.claude/skills/idea/test-fixtures/research-freshness/`: `fresh/` (a
   heading-level stamp within 90 days of a fixed `--today`), `stale/` (a
   heading-level stamp 100+ days before), `no-stamp/` (a heading with
   neither a heading- nor file-level stamp), `file-level-stamp/` (a
   heading with NO stamp of its own, but the file's H1 carries a stamp
   within 90 days of `--today`).
4. Add the `Verified: <today>` stamp to both
   `docs/guides/model-routing.md`'s `## Dispatch authoring: making the
choice explicit` heading and its `## Cross-vendor grounding` heading.

## Acceptance

- [ ] `bash .claude/skills/idea/test-fixtures/research-freshness/check-freshness.sh .claude/skills/idea/test-fixtures/research-freshness/fresh --today <fixed-date>` prints `fresh`
- [ ] `bash .claude/skills/idea/test-fixtures/research-freshness/check-freshness.sh .claude/skills/idea/test-fixtures/research-freshness/stale --today <fixed-date>` prints `stale`
- [ ] `bash .claude/skills/idea/test-fixtures/research-freshness/check-freshness.sh .claude/skills/idea/test-fixtures/research-freshness/no-stamp --today <fixed-date>` prints `absent`
- [ ] `bash .claude/skills/idea/test-fixtures/research-freshness/check-freshness.sh .claude/skills/idea/test-fixtures/research-freshness/file-level-stamp --today <fixed-date>` prints `fresh`
- [ ] `grep -A1 "## Dispatch authoring: making the choice explicit" docs/guides/model-routing.md | grep -qE "^Verified: [0-9]{4}-[0-9]{2}-[0-9]{2}$"`
- [ ] `grep -A1 "## Cross-vendor grounding" docs/guides/model-routing.md | grep -qE "^Verified: [0-9]{4}-[0-9]{2}-[0-9]{2}$"`
- [ ] `bash tests/test_doc_links.sh` still passes after the stamp additions
