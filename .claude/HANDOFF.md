Task: adopt beads (bd) across other repos on this machine — install, update CLAUDE.md/AGENTS.md, convert existing task state to bd issues
Status: not started (new task; distinct from the just-completed architecture pivot)
Next step: read docs/cross-repo-rollout-2026-07-22.md and HUMAN.md's "## Agent-filed blockers" section in this repo, then ask the user which repo(s) to start with and confirm per-repo conversion scope before editing any other repo's tree
Resume with: read this file, then proceed per "Next step" above
Blocking on: nothing technical — needs a scope/order confirmation from the user before cross-repo edits begin (see Gotchas)

## Task

The user asked, in this same conversation: "I want to adopt beads: do
the other repos, update, convert their specs, etc." This is a NEW,
separate task from the architecture pivot this session just finished
(that work — `specs/agentic-core-redesign`, all 15 tasks done/obsolete,
epic `agentic-4t2` closed, pushed to `origin/main` — needs no further
action; do not re-open it).

The new task, concretely: for each other repo on this machine that
should adopt bd —
1. Install bd (once-per-machine: `agentic@agentic-toolkit` plugin +
   `bd` 1.1.0 pinned via `brew install beads`; per-repo: curated
   `bd init`, `/gate` installs the bd-compliance Stop hook,
   `Bash(bd *)` allowlisted) per
   `specs/beads-daily-skill/SPEC.md`'s "Installation in other repos"
   section (this repo, `~/claude`).
2. Update that repo's own `CLAUDE.md`/`AGENTS.md` — many currently
   echo the 2026-07-03 "beads fully retired, use docs/TASKS.md
   everywhere" decision recorded in
   `~/claude/docs/decisions/work-tracking.md`, which this pivot
   reverses for `~/claude` itself but never told other repos to
   revert. **Also add the "record discovered work in bd as you find
   it" convention** (maintainer directive, 2026-07-23) to each
   adopting repo's `CLAUDE.md` — see `~/claude/CLAUDE.md`'s "Beads
   issue tracker" section for the exact wording/command examples to
   adapt (cite `/work`'s SKILL.md there for the runnable commands
   rather than re-deriving them).
3. **Convert** — not just install — each repo's existing
   `docs/TASKS.md` checkboxes / `specs/*/tasks/*.md` markdown task
   state into real bd issues, analogous to what core-redesign task 05
   did for `~/claude` itself (a live import, `python3 -m
   agentic.shadow` there — check whether that tool is reusable
   as-is against another repo's markdown, or needs adapting per-repo).

## State

Nothing done yet on this task. What exists to start from:

- **`docs/cross-repo-rollout-2026-07-22.md`** (this repo) — the audit
  from core-redesign task 15: every repo in `~/REPOS.md` (excluding
  `~/archive/*`), classified with the specific stale phrase or version
  gap found and a recommended action. **Read this first** — it is the
  starting map, not something to redo.
- **`HUMAN.md`**'s `## Agent-filed blockers` section (this repo) —
  per-repo entries task 15 filed for repos needing an attended
  decision. Check what's already there before filing more.
- **bd issue `agentic-m22`** (`specs/beads-daily-skill`, CUJ-5) already
  earmarks `ynab-mcp-server` (`~/ynab-mcp-new` per `~/REPOS.md`) as the
  first live consuming-repo validation target for the install
  procedure — a natural first repo, but confirm against what
  `docs/cross-repo-rollout-2026-07-22.md` actually recommends rather
  than assuming this is still the priority order.
- Candidate repos from `~/REPOS.md` (2026-07-22 snapshot, re-check
  currency — it regenerates daily): `~/automation`, `~/budget_analysis`,
  `~/fooszone`, `~/hub`, `~/interview-prep`, `~/portfolio-tracker`,
  `~/specs`, `~/vaults/life`, `~/ynab-mcp-new`. `~/archive/*` entries
  are already retired — skip them. This list is a pointer to check
  against the rollout doc's real classifications, not an authoritative
  work list on its own.

## Gotchas

- **This is real cross-repo, multi-repo work** — editing other git
  repos' `CLAUDE.md`/`AGENTS.md` and converting their task state is a
  meaningfully larger blast radius than anything scoped to this repo.
  Confirm which repo(s) and what order with the user before mass-
  editing many repos, even though the user has expressed clear intent
  to do all of them — "do the other repos" doesn't specify order,
  simultaneity, or whether each repo's maintainer-judgment call (adopt
  or not) has actually been made yet. `docs/cross-repo-rollout-2026-07-22.md`
  marks some repos "no action needed" — don't force bd onto those.
- **`bd init` has an auto-commit side effect** discovered this
  session: run bare it duplicates a "Beads Integration" block into
  `CLAUDE.md`/`AGENTS.md` and auto-commits without asking. Use
  `--skip-agents` (and curate the AGENTS.md/CLAUDE.md snippet by hand
  afterward) rather than trusting raw `bd init` in any of these other
  repos either.
- **`bd init` also refuses non-interactively if `sync.remote` in a
  committed `.beads/config.yaml` points at an unreachable host** — pass
  `--remote ""` to force a fresh local database when that happens.
- Each of these repos is a **separate git remote/tree** — normal
  cross-session-collision care applies per repo
  (`.claude/rules/concurrent-sessions.md`), and pushing to another
  repo's remote is exactly the kind of action that needs a stated
  go-ahead per this session's general "confirm before pushing"
  practice, not a blanket one-time approval.
- `specs/beads-daily-skill/SPEC.md`'s own CUJ-5 (the ynab-mcp-server
  live run) is still open/manual-pending as of this handoff — it may
  turn out to BE the first step of this larger rollout, or a separate
  narrower validation that should land before doing the rest. Check its
  current status before assuming it's still todo.

## Verification

Nothing from this new task has been attempted yet, so nothing to
verify. The prior architecture-pivot work (a separate, now-closed unit)
was independently verified per-task during this session (verifier
agents re-ran every task's acceptance commands; `bash scripts/check.sh`
green with only the pre-existing documented quarantine) — that
verification stands and does not need repeating.

## Standing convention (maintainer directive, 2026-07-23)

When this task's own work uncovers issues, needs a breakdown, or spots
new work — record it in bd immediately (`bd create`, with a
`discovered-from` link to whatever surfaced it), not just in prose or
a chat reply. Two small examples filed this session, still open and
unrelated to this handoff's own task (fix opportunistically or leave
for a small follow-up): `agentic-d3x` (breakdown/SKILL.md has two
stale post-pivot references — a deleted mirror-check and a deleted
drain-baton generation-budget mention) and `agentic-bsd`
(workboard/SKILL.md line 58 still mentions drain batons). Both are
`~/claude`-local doc drift, not part of the cross-repo task itself.

## Files touched (prior, pivot work — for reference, already committed/pushed)

Not part of this handoff's open task; listed only so a fresh session
doesn't mistake pivot artifacts for something still in flight. See
`git log --oneline eba3640a..4fb3f8c0` in `~/claude` for the full list;
epic `agentic-4t2` is closed at 11/11 children.

Next stage: none — /clear and resume from this handoff file
