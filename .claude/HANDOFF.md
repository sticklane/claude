# HANDOFF: multi-repo session — resume-handoff, human-tasks triage, ynab-triage-skill spec

## Task

This session did four things, in order:

1. Resumed a stale drain-orchestrator handoff (`resume-handoff` skill) and
   synced `~/claude`'s local `main` to `origin/main` (fast-forward, 76aa4e6
   → c632c42; pre-existing uncommitted WIP was stash/pop'd through cleanly).
2. Ran the `human-tasks` skill: swept every `HUMAN.md` across local repos,
   presented a ranked table.
3. Acted on the user's follow-up instructions for that table: dropped
   fooszone-data items, listed `claude`'s 2 open decide-items, attempted
   `automation`'s tasks (found all were genuinely attended-only by their own
   design — see Gotchas), decided `hub`'s goals-domain-split question,
   approved `hub`'s YNAB target plan `2460a5be-1d45-44ad-8855-2047a6b3d932`.
4. User asked to build the "ynab-triage" skill in `automation` (referenced
   but never implemented in `docs/automations/ynab-triage.md`) — ran
   `/idea` → wrote `specs/ynab-triage-skill/SPEC.md` → 4 rounds of
   `/critique` → READY WITH NITS, `Breakdown-ready: true`. **This is where
   it went wrong — see Gotchas, this is the exact-next-step blocker.**

## State

**Done, verified:**

- `~/claude` local `main` = `origin/main` (c632c42 at session start; may
  have moved since).
- `~/hub` `specs/codequality-pkg-mcp-composition/tasks/06-goals-domain-split.md`:
  decided (own `register-goals.ts`, structural not numeric line target),
  committed + pushed (`0b3b0f2`).
- `~/hub` YNAB target plan `2460a5be-…` approved via
  `mcp__hub__ynab_approve_target_plan` (hub-local only — the manual YNAB
  apply checklist was printed to the user in-conversation, NOT re-derived
  here to save tokens; re-run `mcp__hub__ynab_get_target_plan {status:
"approved"}` if it needs to be reprinted).

**In flight / NOT safe to resume blindly:**

- `~/automation` `specs/ynab-triage-skill/` — **live concurrent-session
  collision, unresolved.** See Gotchas. Do NOT touch this repo's git state
  until confirming session `automation-09` (or whatever replaced it) is no
  longer running (`claude agents --json`, look for `cwd:
"/Users/sjaconette/automation"`).
- `~/automation` `HUMAN.md`: my commit `9879c40` (pushed) deleted a blocker
  entry the concurrent drain session had just filed (2026-07-20,
  `specs/ynab-triage-skill/SPEC.md`, decide, NOT READY 3 findings). Never
  restored. Needs a human call on how to reconcile (see Gotchas) — user
  said "let it run" (leave the other session alone) but did NOT yet decide
  how to fix the HUMAN.md/SPEC.md collision itself.

## Files touched this session

- `~/hub/specs/codequality-pkg-mcp-composition/tasks/06-goals-domain-split.md`
  — decided, committed `0b3b0f2`, pushed. Safe, no collision.
- `~/automation/specs/ynab-triage-skill/SPEC.md`,
  `~/automation/specs/ynab-triage-skill/critique-findings.md` — written by
  me (4 critique rounds, READY WITH NITS), committed `9879c40`, **pushed**,
  ON TOP OF a concurrent drain session's own commits to the same path
  (`a320ccd`..`1bdc05f`). My commit also unintentionally carried
  `CLAUDE.md` and `HUMAN.md` diffs I never authored — see Gotchas.
- `.claude/HANDOFF.md` (this file) — new.

## Gotchas / things learned the hard way this session

- **The concurrent-sessions pre-flight check (`.claude/rules/concurrent-
sessions.md`) was skipped before multi-file edits in `~/automation`, and
  it should not have been.** A live interactive session (`automation-09`,
  pid 32044, `cwd: /Users/sjaconette/automation`) was independently working
  the _exact same feature_ (a `ynab-triage-skill` spec) in the _same shared
  checkout_, via what looks like an autonomous `/drain` run: it created its
  own `SPEC.md`, ran `/critique` (NOT READY, 3 findings, 1 round), filed a
  `HUMAN.md` blocker, and released its lease — commits `a320ccd` →
  `1bdc05f` — all landing in the shared local tree while this session was
  also mid-edit in it, unnoticed until after `git push`.
- **Damage done, in order:** my `Write` to `specs/ynab-triage-skill/SPEC.md`
  silently overwrote their draft (mine is more thoroughly critiqued — 4
  rounds vs their 1 — but that's not the point: it was an uncoordinated
  overwrite). My subsequent `git add specs/ynab-triage-skill/ && git commit
&& git push` landed on top of their last commit and the resulting diff
  (`git show 9879c40`) shows `HUMAN.md` losing their just-filed blocker
  entry and `CLAUDE.md` gaining a `## Code navigation (ctx)` section I
  never wrote — meaning the working tree had drifted from what a plain
  `git status` before the add would have shown, almost certainly because
  the other session was actively committing to the same tree in the same
  window. **Root cause never fully reconstructed** — plausibly file-level
  raciness between two sessions writing the same working tree, not a git
  index issue I introduced deliberately.
- **User's explicit instruction on discovering this: "let it run"** — i.e.
  do not intervene in the other session, do not revert anything
  unilaterally, stay out of `~/automation` entirely until it's confirmed
  done. This handoff's exact next step honors that.
- **Every `automation` HUMAN.md task turned out to be attended-only by the
  repo's own design**, not something a session (mine or any other) should
  silently complete: the daily-note-template edit says outright "an agent
  never touches the vault template"; the Gmail OAuth re-auth needs live
  browser consent; `/review-quarter`'s first run and the budget-planning
  session both require Steven's live judgment throughout. Don't try to
  "just do" these on a future ask without surfacing the same constraint.
- **YNAB's REST API: single-transaction update is `PUT
/budgets/{budget_id}/transactions/{transaction_id}`, NOT `PATCH`** — the
  bulk multi-transaction endpoint is `PATCH /budgets/{budget_id}/transactions`
  (confirmed against `api.ynab.com`'s OpenAPI spec this session). The
  critic caught this three separate times across critique rounds before
  the acceptance-criteria grep shape was actually load-bearing — worth
  remembering if any other spec touches the YNAB API.
- **Segmentation acceptance criteria for "module X is the only place that
  writes to service Y" are easy to write vacuously.** Two failed attempts
  this session: host-anchoring the grep (`api.ynab.com` on the same line)
  missed that every existing client in the repo builds URLs from a
  `*_BASE` constant, not an inline host; anchoring on bare
  `requests\.(patch|put|post)` missed that this repo has a _second_ write
  mechanism (`lib/transport.py`'s injectable string-method seam used by
  `lib/todoist.py`/`lib/gmail.py`). The fix that finally worked: pin the
  _implementation_ in the requirement text (mandate `requests.put`
  specifically) so the grep shape becomes load-bearing against a
  now-mandated choice, not just an assumption about existing convention.
- **No officially supported Amazon or Apple API/MCP exists for a personal
  account's own order/purchase history** (confirmed by live web research
  this session) — Amazon's official APIs are seller-side (SP-API Orders,
  Business Integrations MCP); Apple's `mcp-apple-store` is App Store
  Connect/StoreKit for app developers verifying their customers, not a
  consumer's own purchases. Third-party unofficial options exist but want
  either a raw Amazon password in an env var or Playwright scraping — worse
  trust profile than `claude-in-chrome` against an already-logged-in
  session. Worth remembering if this comes up again.

## Verification

- Hub goals-domain-split decision: not run through the `verifier` agent —
  it's a one-line spec decision recorded in a task file's `## Answers`
  section, not implementation code; confirmed by direct `Read` after
  editing, no runnable acceptance criteria apply.
- Hub target plan approval: confirmed via the MCP tool's own response
  (`status: "approved"`, `changeIds` populated) — this is the system of
  record, not something to re-verify independently.
- `automation`'s ynab-triage-skill SPEC.md: critiqued 4 rounds by the
  `critic` agent (not the `verifier` — no implementation exists yet to
  verify, only a spec). Settled verdict READY WITH NITS, recorded in
  `specs/ynab-triage-skill/critique-findings.md` with a content hash. This
  verdict is only meaningful once the collision above is resolved and it's
  confirmed which SPEC.md content is actually the one on disk / at HEAD.
