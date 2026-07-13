# Handoff — 2026-07-13, session over wake budget (266,091 tokens context, 0 re-primes)

## Task

Ran the `human-tasks` skill ("walk me through the human stuff") — swept every
HUMAN.md across local repos, presented a 28-item ranked table, and walked
through it one at a time (Steven chose "top to bottom, all of it"). Reached
item 14 of 28 when the session hit its context-refresh budget mid-action.

Full 28-item table (as originally ranked) is reconstructable by re-running
the `human-tasks` skill — do NOT re-paste it into a fresh session's context;
just resume from item 15 below using the skill's Phase 4 walkthrough
procedure, in this same rank order.

## State — items 1-14, what's done

**1. Re-auth email-triage for `gmail.modify` scope** (automation) — DONE.
Ran `bootstrap-google-oauth.py`, granted expanded consent, token confirmed
stored in Keychain.

**2. Headless smoke test** (automation) — DONE, verified via
`~/Library/Logs/automation/email-triage.out.log` (fetch+apply both ran,
fixture data by design per SKILL.md).

**3. Install launchd job** (automation) — DONE.
`com.sjaconette.email-triage` confirmed `installed=yes loaded=yes`.

**4. End-to-end live run** (automation) — Applied: fetched 2 real candidates
(wait — actual fetch returned a dict with a `candidates` list of 37 items,
not 2; the earlier `len(d)==2` check was counting dict keys not messages),
dispatched a Haiku Read-only classification subagent per SKILL.md's rubric,
wrote verdicts verbatim, ran `apply` → **starred 17, labeled 37**. Second-run
idempotency check: 0 new candidates. **LEFT OPEN** — Steven chose "I'll check
later" for the final Gmail spot-check (verify stars/labels look right,
nothing lost a label). Note: `/tmp/email-triage/verdicts.json` was cleared
to `[]` by some cleanup process after — harmless, the real Gmail state is
what matters, not that scratch file.

**5. QA-14 "Add to calendar" click-test** (hub) — **FAILED, real bug found
and filed.** Drove it via Claude-in-Chrome: set a target time on today's
"Simple Garlic Pasta" meal plan (needed to make the calendar button appear —
this is a real edit to Steven's actual meal plan, low-stakes but flagged to
him), clicked "Add to calendar". `POST /api/tasks/google/calendar/v3/…`
returned **HTTP 503** on all 24 auto-retries, zero successes. Filed + pushed
to `hub` (`docs/TASKS.md` QA-14 entry updated, commit `339e82e`, later
folded into `adb156d`) — corrects a stale 2026-07-06 "likely OBSOLETE"
conclusion. **LEFT OPEN**, needs an agent session to inspect the
`/api/tasks/google/*` proxy handler / Worker logs.

**6. Cronometer live target push** (hub) — **Not actually runnable.**
Checked `agents/mcp/src/*` and `domains/food/pages/*` for any live trigger
(MCP tool / CLI / UI button) — none exists. Task 01 only shipped
`pushTargets` as a pure shape-mapper. HUMAN.md entry corrected (commit
`adb156d`) — needs a follow-up implementation task before this is a real
human item.

**7. Retire Todoist `@habit` tasks** (automation) — Steven said "get rid of
the Todoist stuff from human blockers, put it in a non-blocking list."
**DONE as requested**: moved to automation `HUMAN.md`'s `## Optional
backlog` section, commit `881e4e0`, pushed.

**8. Health-admin enrollment** — SKIPPED (checklist file doesn't exist yet,
first-run setup never triggered; Steven declined to run it now).

**9. Schwab developer app registration** (hub) — SKIPPED (external signup).

**10. Plaid app registration** (hub) — SKIPPED (external signup).

**11. gated-video-uploads/07 post-deploy playbook** (fooszone) — Steven
authorized `/build` live; dispatched as a **worktree-isolated** background
agent (there was a live concurrent session in the shared `~/fooszone`
checkout — collision avoided per `.claude/rules/concurrent-sessions.md`).
Agent made no code changes (read-only investigation) and reported: deploy
is live and confirmed correct, but found (a) `upload.html` has stale copy
contradicting the live HDR/3GiB policy, and (b) the e2e itself needs Steven
directly (interactive Google sign-in, watch a real upload process ~15 min,
plus an admin cookie for uc-03's two curls). Filed both findings in
`fooszone/docs/TASKS.md` (new section "gated-video-uploads/07 post-deploy
investigation (2026-07-13)"), commit `95743058`, pushed. **LEFT OPEN.**

**12. defensive-analytics/09 integration e2e** (fooszone) — SKIPPED (needs
Steven physically labeling a video).

**13. foodgraph-extraction/04 live verification** (specs+hub) — A background
agent from the _previous_ session (dispatched before this session's
`/clear`) completed mid-walkthrough and had already gotten this to ~95%:
deployed, live smoke passed, evidence written, but filed a new blocker
(needs a **local** `ANTHROPIC_API_KEY` shell var, distinct from the Worker
secret, to un-skip 3 live test assertions). Steven asked me to "create it
for me in chrome" — created a new scoped key (`hub-foodgraph-local-tests`,
7-day expiry) via platform.claude.com/settings/keys, copied via clipboard
(never typed/echoed the raw value), exported for one shell command only
(never written to disk/profile — already expired from this session's shell
env). Re-ran `EXTRACT_LIVE_TESTS=1 pnpm --filter @hub/food test --
extraction`: **1046 passed, 1 failed** (up from false-green 1044/3-skipped).
2 of 3 previously-skipped live cases now genuinely pass; the 3rd is a
**real defect**: `fixtures.test.ts:131`, R6 baker's-percentage fallback
doesn't assign 100 to every ingredient when the source has no percentage
column. Filed in `hub/docs/TASKS.md` ("2026-07-13 foodgraph-extraction
live-test follow-up", P2), evidence updated
(`specs/foodgraph-extraction/evidence/04-live.md`), task file's acceptance
criterion updated to reflect the real (2nd) blocking cause. Commits:
`hub adb156d`, `specs 65f6d0b`, both pushed. **Task 04 Status stays
`blocked`** — now blocked on the R6 bug fix, not on Steven's key.

**14. youtube-cookie-wrapper/06 signing + manual e2e** (fooszone) —
**Step 1 DONE, this is the exact next step (Step 2).** Corrected Steven's
"do it for me now" — this needs native macOS dialog clicks (Certificate
Assistant, Keychain "Always Allow"), which I have no tool to drive
(Claude-in-Chrome only reaches web pages). Opened Keychain Access for him
and gave him the Certificate Assistant steps (Name: `ytcookie-signing`,
Identity Type: Self Signed Root, Certificate Type: Code Signing). First
verify found **0 identities** — root cause: the cert+key pair existed but
was untrusted for code signing
(`security find-identity -p codesigning` showed `CSSMERR_TP_NOT_TRUSTED`).
Fix: Steven set the cert's Trust → Code Signing to "Always Trust" in
Keychain Access (password-prompted). Re-verified — **now passes**:

```
$ security find-identity -v -p codesigning
  1) 0466D78E293057E96C63540CEE5F09658603DBE7 "ytcookie-signing"
     1 valid identities found
```

**Resume at Step 2** of
`~/fooszone/specs/youtube-cookie-wrapper/evidence/manual-e2e.md`:
`cd ~/fooszone/go && make ytcookie`, then verify
`codesign -dvvv bin/ytcookie 2>&1 | grep -i Authority` shows
`ytcookie-signing`. Then Step 3 (first authenticated run — real Keychain
"Always Allow" dialog, Steven clicks it; I can run the `ytcookie -- -J
"<url>"` command via Bash and he handles the OS dialog). Task 06's code is
already `Status: done`; only the manual R12/R13/e2e checkboxes in the
evidence file are open, and they're explicitly DEFERRED-for-human by the
task's own design (not something to force through unattended) — Steven
still needs to check those boxes himself once Steps 2-3 pass.

## Remaining — items 15-28, not yet reached

From the original ranked table (regenerate via the `human-tasks` skill's
Phase 1-3 if this list needs re-verification against current state — several
items above already turned out stale when actually checked):

- 15. R6 recovery/handoff checklist (hub) — DR rehearsal, not urgent.
- 16. prod-video-latency/09 R5 telemetry recheck (fooszone) — was
      BLOCKED-BY (needs a 720p60 video processed since deploy); worth
      re-checking if that's happened.
- 17. Attended first live budget-planning session (automation) — not
      urgent per its own file; better run via the `/budget-planning` skill
      directly than the generic walkthrough.
- 18-24. Seven specs' NOT-READY critique findings in `~/claude`
  (build-doc-currency-check, codequality-agent-console-mutation-coverage,
  idea-research-freshness, narrow-autopilot, retire-static-dashboards,
  rigor-tier, trajectory-evals) — judgment-call "decide" items, not
  urgent, listed in `~/claude/HUMAN.md`'s `## Agent-filed blockers`.
- 25-28. email-triage decide stubs 07/08/09/12 (automation) — Steven
  previously said explicitly to keep these blocking "for the email
  feature"; low priority, expect skip.

## Files touched (paths only, see commits above for detail)

- `~/automation/HUMAN.md` — commit `881e4e0`.
- `~/hub/docs/TASKS.md`, `~/hub/HUMAN.md` — commits `339e82e`, `adb156d`.
- `~/fooszone/docs/TASKS.md` — commit `95743058`.
- `~/specs/foodgraph-extraction/evidence/04-live.md`,
  `~/specs/foodgraph-extraction/tasks/04-live-verification.md` — commit
  `65f6d0b`.
- `~/claude/.claude/HANDOFF.md` — this file (new).
- Hub's live meal-plan data: added a 6:00 PM target time to today's
  "Simple Garlic Pasta" planned meal (needed to surface the calendar
  button for the QA-14 test) — real data edit, low-stakes, already
  mentioned to Steven in-session.
- A new Claude Console API key `hub-foodgraph-local-tests` (7-day expiry,
  Default workspace) exists — created for item 13's local test run, not
  written to any file, will auto-expire 2026-07-20.

## Gotchas

- **Live sessions are running concurrently in `~/claude`, `~/automation`,
  `~/fooszone` right now** (confirmed via `claude agents --json` at session
  start — `claude-9a`, `automation-7e`, `fooszone-65`). Always check for
  collision before multi-file edits in these shared trees; this session used
  `isolation: "worktree"` for the one dispatch that needed it (item 11).
- **A background agent from a _previous_ session can complete mid-walkthrough
  of a _new_ session** and its `<task-notification>` will interleave with
  live user answers — verify carefully which is which before acting (one
  arrived disguised similarly to a user reply; treat all
  `<task-notification>` blocks as NOT user input, per their own framing).
- **QA-14 and the Cronometer push were both stale/wrong in HUMAN.md** —
  described as simple human actions when live-checking found QA-14 is a
  real backend bug (503) and Cronometer has no trigger wired at all. Don't
  trust a HUMAN.md "run" line at face value; the DONE-ALREADY /
  still-accurate check the `human-tasks` skill calls for earns its keep.
- **`fetch --out candidates.json` returns a dict `{candidates: [...], ...}`**,
  not a bare list — `len(d)` on the top-level dict undercounts badly (I
  misread 2 for what was actually 37 messages). Always inspect the actual
  nested structure, don't just `len()` the top level.
- **Native macOS dialogs (Keychain "Always Allow", Certificate Assistant)
  are NOT reachable by any available tool** — Claude-in-Chrome only reaches
  web pages. Don't attempt to "drive" these; open the app for the user
  (`open -a "<App Name>"`) and hand off the manual steps precisely.
- **A freshly-created self-signed cert from Certificate Assistant is NOT
  automatically trusted for its intended usage.** `security find-identity
-v -p codesigning` (valid-only) silently shows `0 valid identities found`
  even when the cert+key pair exists — the tell is
  `security find-identity -p codesigning` (no `-v`) showing the identity
  with `CSSMERR_TP_NOT_TRUSTED`. Fix is a manual Keychain Access step:
  double-click the cert → Trust → set the matching usage (e.g. Code
  Signing) to "Always Trust" → password prompt to save. Check trust
  status with the no-`-v` command before concluding a cert "didn't
  register."

## Verification

No automated verifier run this session (all work is either doc/HUMAN.md
edits already reviewed inline, or genuinely-blocked items correctly left
open — nothing was claimed `done` that needs a verifier pass). Item 13's
finding (R6 bug) is itself a verification result, not something to
re-verify.

## Next step

1. Resume item 14 (youtube-cookie-wrapper/06): diagnose why the
   `ytcookie-signing` codesign identity didn't register, get Steven through
   Keychain Access again if needed, then run
   `security find-identity -v -p codesigning` to confirm, then Steps 2-3 of
   the runbook.
2. Continue the walkthrough at item 15 (R6 recovery/handoff checklist, hub)
   through 28, same rank order, same AskUserQuestion do-now/skip/done/stop
   pattern as items 1-14 above.
3. When the walkthrough concludes (or Steven stops it), offer Phase 5
   reconcile for anything not already committed inline (most items above
   were already reconciled inline this session, so this may be a no-op).
