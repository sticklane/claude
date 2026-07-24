Task: specs/bd-native-handoffs — redesign session-handoff mechanism to be bd-native
Status: in-progress
Next step: write specs/bd-native-handoffs/SPEC.md (interview + scouting already done — see bd issue agentic-3ol's --design field for the full decided design, verified bd commands, and file-by-file scout findings; do NOT re-interview or re-scout), then continue the /idea skill flow: step 5 (skip /design — no open tech/arch question expected), step 6 /critique loop until READY, step 7 self-chain /breakdown
Resume with: /resume-handoff
Blocking on: nothing
Tracked: agentic-3ol

## Task

User asked (mid-session, after questioning the design) to redesign this
repo's session-handoff mechanism: retire the free-standing `HANDOFF.md`
prose file in favor of bd issue fields/comments, matching beads' own model
(`bd create/update --design`/`--notes`, `bd prime`'s context-recovery
philosophy) instead of the current hybrid (bd tracks work-item state via a
`Tracked:` header, but session narrative stays in markdown prose). This
session ran the `/idea` skill: scouted, interviewed the user, and got a
fully decided design — but hit a session-refresh wake-budget trigger before
writing the actual `specs/bd-native-handoffs/SPEC.md` file. Nothing has
been written to `specs/` yet.

## State

**DONE this session, unrelated to the handoff redesign (all committed and
pushed, do not re-touch):**
- Synced `~/claude` to `origin/main` (was 23 commits behind).
- 9 local repos (fooszone, hub, automation, portfolio-tracker,
  ynab-mcp-server, interview-prep, budget_analysis, specs, vaults/life)
  already had bd fully converted from a prior session; this session found
  and fixed post-cutover doc drift in all 9 via a Workflow-tool pipeline
  (`wf_db4fb6c5-245`) — bloated/duplicate CLAUDE.md, and a byte-identical
  generic bd-cheatsheet AGENTS.md in 6 of them replaced with real
  purpose/Map/Commands/State orientation. 8/9 passed independent
  verification; ynab-mcp-server's dist/ build-artifact drift (pre-existing,
  unrelated to the doc edits) was fixed with a real rebuild+commit
  (`d52ca27`) and re-verified clean in this handoff's own verifier pass
  (see Verification section).
- `~/archive/*` repos deliberately left un-converted (user confirmed:
  dormant/archived on purpose, not worth a bd cutover).
- Read and converted 3 stray, never-consumed `.claude/HANDOFF-*.md` files
  from older sessions into bd issues (`agentic-oip`, `agentic-d3a`), then
  deleted them.
- Checked all 4 installed plugins for updates (`agentic`/`cloudflare`/
  `prompt-improver` already latest; `frontend-design` refreshed, needs a
  Claude Code restart to apply — same as a few days ago, still pending).
- Widened `bin/check-token-discipline`'s `IN_SCOPE` to cover all 4 saved
  `.claude/workflows/*.js` scripts (previously only `deep-research.js` was
  checked) and taught `TIER_RE` to recognize `agentType:` as a valid tier
  signal (it previously only recognized prose like "haiku"/"effort").
  Confirmed by direct inspection: every workflow script already tiers
  correctly. Two smaller real gaps (missing output-budget language in 4
  scripts, a couple of paragraph-adjacency false positives in dense JS)
  filed as `agentic-gqs` rather than fixed inline. Committed `072293a8`.

**IN FLIGHT — the actual next-step work (nothing written to specs/ yet):**
The `/idea` skill's scout (3 parallel scouts) and interview
(`AskUserQuestion`, 4 questions) are both complete. The full decided
design, verified bd CLI command syntax, and a file-by-file list of every
file the redesign touches are all recorded in bd issue `agentic-3ol`'s
`--design` field — read `bd show agentic-3ol` (or `--json` for the raw
field) rather than this file re-deriving it. Short summary: an explicit bd
`handoff` label marks the signal (not reused claimed-status, not a custom
issue type); each still-open touched issue gets a `bd comment` state
update; one lightweight new bd issue per parking event holds the
cross-cutting narrative (`--design`/`--notes`) and links to tracked issues
via `bd dep add ... -t tracks`; scope is one spec covering
handoff/resume-handoff skills, the SessionStart hook, workboard.py,
agent-console.py, their tests, and doc updates (token-discipline.md,
context-management.md, external-playbooks.md, AGENTS.md); rigor is
production; no backward-compat shim (zero legacy HANDOFF.md files exist
anywhere in scope).

## Files touched

- `bin/check-token-discipline` — IN_SCOPE widened, TIER_RE taught
  `agentType`. Committed `072293a8`.
- `/Users/sjaconette/ynab-mcp-new/dist/{index.js,tools/ynabUtils.js,registerTools.js}`
  — rebuilt to match `src/registerTools.ts` split. Committed `d52ca27`,
  pushed, re-verified this handoff.
- 9 external repos' `CLAUDE.md`/`AGENTS.md`/`README.md` — see workflow
  journal at
  `/Users/sjaconette/.claude/projects/-Users-sjaconette-claude/d1606413-d900-4d7b-b3de-a5edde4cd4ce/subagents/workflows/wf_db4fb6c5-245/journal.jsonl`
  for the full per-repo diff list; all pushed.
- No files touched yet for the handoff redesign itself — `specs/` is
  untouched, this is the very next action.

## Gotchas

- **The session's own scratch/tmp disk filled up mid-turn** (`ENOSPC` on
  every Bash call, including `echo test`) — almost certainly the earlier
  18-agent/1.17M-token Workflow run's transcript data. User fixed it
  externally ("ok fixed"); shell tool confirmed working again with a
  sanity check before resuming. If this recurs, it's an environment issue
  outside agent control — surface it plainly, don't retry blindly.
- **`bd prime` does NOT surface per-issue notes/design/comments
  automatically** — confirmed via scout: it returns queue-shaped output
  (ready list, stats, workflow reminders), not per-issue content. A fresh
  session resuming a bd-native handoff needs an explicit
  `bd show <id> --json --include-comments` call. This directly shapes the
  redesigned `resume-handoff` skill's step 2.
- **`--design` has no append mode** (full replacement only via
  `bd update --design`); `--notes` has `--append-notes` for one-shot
  appends; `bd comment <id> "..."` is the genuinely append-only,
  timestamped, multi-session-safe log. Don't conflate the three when
  writing the redesigned skill's exact command sequence.
- **`bd doctor` doesn't work in this repo's embedded-Dolt mode** ("not yet
  supported in embedded mode") — don't reach for it here; use
  `bd list --json` / direct file checks instead if a future session needs
  to sanity-check bd state.
- **This repo's `.beads/config.yaml` deliberately has no `sync.remote`
  configured** — that's a legitimate per-machine choice per the config
  file's own comment (not a bug to fix), so the recurring "no Dolt remote
  configured" warning on every `bd` write is expected noise, not a defect.
- The scout sweep found the redesign's blast radius is considerably wider
  than the original framing (which assumed just the two skills + one
  hook) — `workboard.py`'s `scan_handoffs()` and `agent-console.py`'s
  `dispatch-resume-handoff` action both glob `HANDOFF*.md` too, with their
  own test suites. The user explicitly chose to include these in one spec
  rather than deferring — don't re-litigate that scope decision.

## Decisions

- **Explicit `handoff` bd label over reusing claimed-status, and over a
  custom issue type.** Why: reusing "claimed but open" as the signal would
  make ordinary in-progress work indistinguishable from a deliberately
  parked handoff; a custom issue type needs `types.custom` config
  (friction bd's native `--labels` mechanism avoids). User confirmed this
  option explicitly over the alternative in the interview.
- **Per-issue `bd comment` PLUS one lightweight tracking issue, not
  either alone.** Why: a single comment-only approach loses the
  cross-cutting narrative that doesn't belong to any one issue (concurrent-
  session warnings, batch verification status); a single tracking-issue-
  only approach loses the up-to-date state on each individual piece of
  work. User's own answer synthesized both rather than picking one of my
  two offered options — captured verbatim in `agentic-3ol`.
- **Full scope in one spec (skills + hook + workboard.py + agent-
  console.py), not a deferred fast-follow.** Why: user explicitly chose
  "include now" over my recommended "defer" option when I flagged the
  wider blast radius — don't second-guess this by scoping down when
  writing the SPEC.md.
- **No backward-compat shim for legacy `HANDOFF.md` files.** Why: verified
  zero exist anywhere in `~/claude`'s scope as of this session (the last
  ones were consumed this session), and handoff/resume-handoff are
  plugin-distributed skills rather than per-repo-copied files, so no other
  repo needs a migration path either. A clean cutover avoids maintaining
  dead fallback code for a case that doesn't occur.
- **Filed `agentic-gqs` instead of fully fixing the token-discipline
  checker's remaining gaps inline.** Why: fixing the real bug (missing
  `agentType` recognition) was cheap and directly answered the user's
  question; auditing/adding output-budget language to 4 already-executed
  workflow scripts is separate, lower-urgency work that would have
  delayed the higher-priority handoff-redesign interview the user was
  waiting on.

## Verification

- `bin/check-token-discipline` fix: `tests/test_check_token_discipline.sh`
  passes 55/0 before and after the edit; the bare script's remaining
  real findings are filed in `agentic-gqs`, not silently dropped.
- ynab-mcp-server dist rebuild (`d52ca27`): independently re-verified by a
  fresh `verifier` agent this handoff — pass:true on all 5 checks (commit
  present + pushed, `npm run build` reproduces a clean tree, gate green,
  `dist/registerTools.js` is real compiled output). No open concerns.
- 9-repo doc-cleanup workflow: 8/9 repos passed their own in-workflow
  verifier pass with zero failures; budget_analysis and vaults/life each
  had one non-blocking pre-existing-and-disclosed untracked-file note (not
  a defect). ynab-mcp-server's one real failure (dirty dist/) is the item
  fixed and re-verified above.
- The handoff-redesign spec itself: nothing to verify yet — no SPEC.md
  written, no code changed. `## Open questions` doesn't exist yet because
  the file doesn't exist yet.

Next stage: none — /clear, then /resume-handoff picks the work up.
