# Decision record: work-tracking consolidation (beads → hybrid)

Date: 2026-07-03
Source: `~/specs/work-tracking-consolidation/SPEC.md` (audit 2026-07-03, three
scout/research reports; decisions recorded by the authoring session while Steven
was away — cheap to flip, revise the spec first if so).

## Audit evidence

bd (beads 1.0.4) was mandated in 8 repos' CLAUDE.md files and primed into every
Claude Code session via global `~/.claude/settings.json` hooks (~2–4k
tokens/session), but the 2026-07-03 audit found it genuinely load-bearing in only
two repos: **fooszone** (536 issues, 166 open, active dependency graph) and
**interview-prep** (17 fresh open job-hunt issues migrated from
resume-and-jobhunt on 2026-07-02/03). Everywhere else it was ceremonial:
tasks-app had 756 issues with 1 open (dead since March 2026), portfolio-tracker
348 with 2 open, the shared daemon had been down since February, Dolt sync was
abandoned 2026-07-02, `bd remember` was never used once, and the home `~/.beads`
was never initialized for issue creation (`bd create` fails with "issue_prefix
config is missing").

## Decision

**Hybrid.** Keep bd in fooszone and interview-prep, where it earns its keep;
everywhere else, decommission it in favor of markdown `docs/TASKS.md` checkboxes
for small work and the `specs/` + `/breakdown` flow for larger work. Global
`bd prime` SessionStart/PreCompact hooks removed from `~/.claude/settings.json`;
the two keeper repos carry repo-local prime hooks instead. Issue data in
decommissioned repos is archived as committed `docs/beads-archive.jsonl`
(verbatim JSONL); only non-closed issues were converted to markdown.

## Upstream situation

Beads 1.0 pivoted to a Dolt backend, which broke pre-1.0 users (legacy
`beads.db` layouts risk an in-place Dolt migration on any bd invocation — the
reason decommissioning never ran `bd` in legacy repos). The project has moved to
the Gas Town organization and now primarily serves Yegge's Gas Town multi-agent
orchestrator — a scale mismatch for solo use.

- beads: <https://github.com/gastownhall/beads> (formerly `steveyegge/beads`,
  which redirects there; verified 2026-07-03)
- Gas Town: <https://github.com/gastownhall/gastown> (verified 2026-07-03)

No local research-report file exists on disk (checked 2026-07-03), so the links
above are the primary sources.

## Revisit trigger

Reconsider if a keeper repo's bd breaks on a future bd upgrade, or if
docs/TASKS.md proves insufficient in two or more repos.

## Interview-prep promotion

interview-prep was promoted to keeper on evidence (17 fresh open issues) during
the critic pass — a departure from the original "fooszone only" framing.
Confirmed by Steven 2026-07-03.
