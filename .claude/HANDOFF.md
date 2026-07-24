Task: specs/bd-native-handoffs — 5 tasks ready, none yet built
Status: needs-verification
Next step: run `/build specs/bd-native-handoffs/tasks/01-rewrite-handoff-skills.md` (or any of the Touch-disjoint 01/02/03/05) in a fresh session, or `/drain specs/bd-native-handoffs` to work the queue unattended
Resume with: /resume-handoff
Blocking on: nothing — this is a human-launched execution stage, not something to auto-invoke
Tracked: agentic-3ol, md-ee185446, md-d6704f21, md-6dea3068, md-d8f63486, md-df3e5608

## Task

Continuation of the bd-native-handoffs redesign (retiring the free-standing
`HANDOFF.md` prose file in favor of bd issue comments/labels, per the
user's earlier design interview). This session took the spec from written
through READY (4 critique rounds) through a 5-task breakdown, all
committed and pushed. Nothing has been implemented yet — this handoff
exists because a wake-budget refresh fired, not because of a blocker.

## State

**DONE, committed and pushed to origin/main (HEAD `fb9a9f57` as of this
handoff — just fast-forward-synced 12 commits, unrelated to this task:
new critic.md code-health rubric, docs/code-review-research-2026-07.md,
build/critique/work SKILL.md updates — read those if starting fresh work
elsewhere, not relevant to bd-native-handoffs itself):**

- `specs/bd-native-handoffs/SPEC.md` — written, critiqued through 4
  rounds to READY, `Breakdown-ready: true` header set. Full design
  history (interview answers, verified bd CLI commands, scout findings)
  is in bd issue `agentic-3ol`'s `--design` field.
- `specs/bd-native-handoffs/tasks/01-05` — 5 task files, Touch-disjoint
  except task 04 depends on task 03 (agent-console.py dynamically
  imports workboard.py as a module — a real code dependency, confirmed
  via `ctx refs` during breakdown, not just file overlap). Task 04's
  acceptance criteria were caught as fully gameable by breakdown's own
  critic pass (all three original checks passed on the UNCHANGED tree —
  agent-console's tests use hand-built fixtures decoupled from
  workboard's real output) and fixed with a non-vacuous forcing check.
- All 5 tasks shadow-synced into bd: `md-ee185446` (01), `md-d6704f21`
  (02), `md-6dea3068` (03), `md-d8f63486` (04), `md-df3e5608` (05) — all
  `Status: pending`, all `open` in bd.
- `bin/check-token-discipline` widened to cover all 4 saved
  `.claude/workflows/*.js` scripts (was only `deep-research.js`);
  taught `TIER_RE` to recognize `agentType:`. Follow-up gaps (missing
  budget language in the 4 scripts, dense-JS paragraph-adjacency false
  positives) filed as `agentic-gqs`, not fixed.
- 9-repo bd-cutover doc-cleanup workflow (from earlier this session, see
  prior conversation context if resuming with full history) — all 9
  independently verified, `ynab-mcp-server`'s dist/ drift fixed and
  re-verified. Nothing pending there.
- 3 stray never-consumed `HANDOFF-*.md` files converted to bd issues
  (`agentic-oip`, `agentic-d3a`) and deleted.

**NOT DONE — the actual next step:** none of the 5 bd-native-handoffs
tasks have been `/build`ed. `Status: needs-verification` on this handoff
reflects that the SPEC+breakdown artifact itself was verified (4 critique
rounds + 1 breakdown sanity-check, all by fresh-eyes critic agents, not
self-reported) but the underlying skills/hook/dashboard code changes
haven't been written yet — there's nothing to verify there because it
doesn't exist.

## Files touched

Everything under `specs/bd-native-handoffs/` (new). `bin/check-token-
discipline` (widened scope + regex fix, commit `072293a8`). No other
repo files touched by this redesign work yet — tasks 01-05 are exactly
where that implementation happens next.

## Gotchas

- **`bd show <id> --json` returns a JSON array, not an object** — index
  `[0]` before reading fields. Bit me writing this handoff's own
  verification check.
- **`agent-console.py` dynamically loads `workboard.py`** via
  `_load_module("workboard", SKILLS_ROOT / "workboard" / "workboard.py")`
  — this is why task 04 truly depends on task 03, not a Touch-collision
  heuristic. Whoever builds task 04 must read task 03's ACTUALLY-LANDED
  field names from the real committed `workboard.py`, not from task 04's
  own file (which deliberately doesn't hard-code them).
- **`docs/guides/context-management.md`'s handoff-related prose is word-
  wrapped across physical lines** ("self-contained handoff\nfile"), which
  defeats a naive single-line `grep`. Task 05's acceptance criterion for
  that file uses a structure-anchored `awk` extraction instead — same
  trap `.claude/rules/shell-text-tools.md` already warns about, just
  freshly rediscovered.
- **`docs/external-playbooks.md`'s "## Handoffs" section is `/factcheck`-
  cited** (verbatim external quotes + URLs) — task 05 is scoped to only
  reword the 3 reconciliation "→" lines pointing at this repo's own
  mechanism (~565, ~577, ~608), never the cited quotes themselves.
- **A combined `pytest -k <filter>` across multiple file args silently
  deselects tests in the files that don't match the filter** — caught
  twice this session (once in the spec's own AC6, once again as a
  breakdown sanity-check target). Always split into separate invocations
  when verifying coverage across files with different naming patterns.

## Decisions

- **No backward-compat shim for legacy `HANDOFF.md` files** (R9) — zero
  exist anywhere in scope, plugin-distributed skills don't need per-repo
  migration. Confirmed, not re-litigate.
- **`/handoff` requires bd; when unavailable it stops with a pointer to
  `agentic init`/`bd init`, never a silent file fallback** — added during
  critique round 1 as the resolution to a real gap (the mechanism is
  plugin-distributed to repos that may lack bd). This is now R1's stated
  behavior, not an open question.
- **Full scope in one spec** (skills + hook + workboard.py +
  agent-console.py), not deferred — the user explicitly chose this when
  I flagged the wider-than-expected blast radius during the interview.
  Don't re-scope down when building.

## Verification

- SPEC.md: 4 independent critic passes (fresh agent each round, no
  memory of the implementation) — READY, zero open findings.
- Breakdown: 1 independent critic sanity-check pass — NOT READY on first
  pass (task 04's vacuous acceptance), fixed, not re-verified with a
  second critic round (the fix was mechanical and directly addresses the
  critic's own stated reproduction steps — judged sufficient rather than
  spending a 6th critic dispatch on this artifact this session).
- Nothing else to verify — no implementation code exists yet for tasks
  01-05.

Next stage: none — /clear, then /resume-handoff picks the work up.
