# Task 15: cross-repo rollout — propagate the pivot to other repos on this machine

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch, Rigor) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Priority values run P0 (highest) through P3; the header is optional — absent means P2. -->
<!-- Status vocabulary: pending → in-progress → done; also blocked (always with an Unblock: line), deferred, skipped, draft (stub awaiting promotion), and needs-verification (implementation complete, acceptance unverified — the verifier flips it to done; scanners treat it as open agent-bounded work, never a needs-attention flag). -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers, in every task file — and ## Progress / ## Deferred questions are drain-written sections (single writer, main checkout): workers report that content, never write it. -->

Status: done
Depends on: none
Priority: P2
Rigor: prototype
Budget: 20 turns
Spec: ../SPEC.md (2026-07-22 addendum); specs/beads-daily-skill/SPEC.md ("Installation in other repos")
Touch: docs/cross-repo-rollout-2026-07-22.md, HUMAN.md

## Goal

The 2026-07-22 pivot changes two things every other repo on this
machine may need updated for: (a) this repo distributes as the
`agentic` plugin, which auto-updates via each consuming repo's own
`plugin-autorefresh` hook — verify that still holds rather than
assume it; (b) `docs/decisions/work-tracking.md`'s 2026-07-03 "full
exit" decision told every repo to drop bd for markdown
`docs/TASKS.md`. This repo now reverses that for itself
(`specs/beads-daily-skill`). Other repos were never told to revert —
each needs its own repo-local install decision.

This task does NOT edit other repos' git trees directly — that is
cross-repo, higher-blast-radius work outside this repo's scope and
each target repo's own maintainer judgment. It produces the audit
and the per-repo checklist; the actual per-repo edits are follow-on
work, filed so they are not lost.

## Touch

Read-only over every other repo (via `~/REPOS.md` and read access to
their `CLAUDE.md`/`AGENTS.md`, never a write). Writes only inside
this repo: the rollout document and `HUMAN.md`'s agent-filed-blockers
section (per `.claude/rules/human-blockers.md`).

## Steps

1. Enumerate candidate repos from `~/REPOS.md` (the daily-refreshed
   local index) — every row with a local clone, excluding
   `~/archive/*` (already retired).
2. For each, read its `CLAUDE.md`/`AGENTS.md` (already on disk;
   `~/REPOS.md`'s AGENTS/CLAUDE columns say whether the files exist)
   and classify: (a) references beads/`bd` in a way that predates or
   contradicts this pivot (e.g. echoes the 2026-07-03 full-exit
   decision, or has no bd mention despite being a real candidate),
   (b) plugin version currency — does its `.claude-plugin` lockfile
   or install note reference an `agentic` version older than this
   repo's current `plugin.json`, (c) no action needed.
3. Write `docs/cross-repo-rollout-2026-07-22.md`: one row per
   candidate repo — classification, the specific stale phrase (quoted)
   or version gap found, and the recommended action, referencing
   `specs/beads-daily-skill/SPEC.md`'s "Installation in other repos"
   steps for any repo recommended for bd adoption.
4. File one `HUMAN.md` blocker entry per repo needing an attended
   edit, per the entry grammar in `.claude/rules/human-blockers.md`
   (plain-language action, a `Blocks:` clause) — not one vague
   umbrella entry.
5. `specs/beads-daily-skill`'s CUJ-5 (bd issue `agentic-m22`) already
   covers a live install run on one consuming repo
   (`ynab-mcp-server`); cross-reference it rather than duplicating
   that work here.

## Acceptance

- [x] `test -f docs/cross-repo-rollout-2026-07-22.md && echo EXISTS` → `EXISTS`
- [x] the rollout doc lists every non-archived repo from `~/REPOS.md` (verify: repo count in the doc's table ≥ the non-archive row count in `~/REPOS.md` at this task's base commit)
- [x] `grep -c "^- \[ \] .* · run\|^- \[ \] .* · ask\|^- \[ \] .* · provision\|^- \[ \] .* · decide" HUMAN.md` → increased by exactly the number of repos the rollout doc marked "attended edit needed" (no silent drop, no vague umbrella entry)
- [x] every `HUMAN.md` entry this task adds has a non-empty `Blocks:` clause (per `.claude/rules/human-blockers.md`)
- [x] `git status --porcelain -- $(git rev-parse --show-toplevel | xargs -I{} echo {}) | grep -v '^ M docs/cross-repo-rollout\|^ M HUMAN.md\|^?? docs/cross-repo-rollout'` confirms no file outside this task's Touch changed (no other repo's tree was written)
- [x] `bash scripts/check.sh` → green

Evidence (2026-07-22 run): doc docs/cross-repo-rollout-2026-07-22.md — 11-row table = 11 non-archive REPOS.md rows; classified 4 repos (automation, fooszone, interview-prep, portfolio-tracker) as attended-edit → 4 HUMAN.md `decide` entries (count 8→12, each with a Blocks: clause); ynab-mcp-server cross-referenced to beads-daily-skill CUJ-5 (agentic-m22) not re-filed; plugin version dimension no-op (no repo pins an agentic version, machine-global cache auto-refreshes via ~/claude's plugin-autorefresh hook — verified, not assumed). `bash scripts/check.sh` → green (exit 0).

Depth ceiling: L1 — the per-repo classification is editorial judgment
a human review confirms; the mechanical complement is the acceptance
checks above (doc exists, every repo covered, every filed item has a
`Blocks:` clause) plus task 12's audit job over time.
