# Handoff — 2026-07-14, session over wake budget (258k tokens, 0 re-primes)

## Task

Two threads, both mid-flight:

1. `/agentic:drain` (no-argument, whole `specs/` queue) launched by Steven.
   It is DEEPLY unattended-nested right now: this session spawned
   generation 2 as an awaited background Agent, which itself batoned to
   generation 3 (and possibly further) the same way. **Do not manipulate,
   kill, or duplicate this — Steven explicitly said "don't manipulate any
   agents."** Just let it keep running; it's self-supervising via the
   baton-pass chain and will report when the whole queue is exhausted.
2. Steven asked for a spec on context-usage problems (particularly the
   `/agentic:workboard` relay dumping raw scan JSON into the calling
   session), then a workboard UX/accuracy testing pass (browser + frontend
   work on agent-console), deferred until a fresh session picks this up.

## State — what's done

**Drain queue (this run, Run-token `6024dfeafbc418c5`):**

- `drain-worktree-isolation-hardening`: tasks 01-05 DONE, merged, spec
  review skipped (docs-only), lease released. One discovered draft stub:
  `specs/drain-worktree-isolation-hardening/tasks/06-codex-mirror-code-span-wrap.md`
  (cosmetic, low priority). One MANUAL-PENDING item from task 05: a human
  needs to attended-run `/drain` to live-verify R1/R3/R4 behavior,
  transcripts to that spec's `evidence/` dir — not yet done.
- `skill-doc-size-guards`: fully done (gen 2), spec review 0 findings,
  lease released.
- `agentprof-attribution-gaps`: task 09 done (gen 3), spec review 0
  findings, lease released.
- `critique-findings-loop-closure`: task 01 done (gen 3, added
  MECHANICAL/JUDGMENT findings triage to `/critique`).
- **Currently in-progress as of last check**: `drain-worker-dispatch-hardening`
  task 01, claimed by generation 3. `bash specs/status.sh` showed
  `done: 50, draft: 2, in-progress: 1, obsolete: 8, pending: 18` most
  recently.
- **Anomaly**: two `DRAIN-OWNER.md` files exist simultaneously (both
  Generation 3, same Run-token) — `specs/drain-worker-dispatch-hardening/`
  and `specs/critique-findings-loop-closure/`. The latter's spec (tasks
  02-04) is NOT exhausted, so its lease should still legitimately be held,
  but drain's own doctrine says "at most one dispatch lease at a time"
  (transient overlap only for 3b/critique-intake). This looks like the
  successor generations interpreted the global priority tie-break as
  license to hold two specs' leases at once rather than draining one spec
  to exhaustion before claiming the next (which is what generation 1, this
  session, did). Not urgent — W=1 means only one worker is ever actually
  dispatched — but worth a look if the exit checklist seems off, or if a
  concurrent drain refuses claiming either spec citing FRESH-but-foreign.
- Two prior generations' `DRAIN-BATON.md` files were never cleaned up:
  `specs/agentprof-attribution-gaps/DRAIN-BATON.md`,
  `specs/skill-doc-size-guards/DRAIN-BATON.md`. The workboard scanner flags
  both as "unparsable relaunch command" (a scanner-format nit — my
  hand-authored batons didn't include a machine-parsed relaunch-command
  block; check whether reference.md's Baton pass section actually
  specifies one I missed, or whether the scanner's expectation is stale).

**New/amended spec**: `specs/context-blowout-subagent-guards/SPEC.md` —
added a third incident (workboard-relay context blowout) plus R5-R8
(a `token-discipline.md` delegation bullet + a scout-dispatch rewrite of
`/workboard`'s "Relay the inbox" step), updated Out of scope, Acceptance
criteria, Parallelization, Open questions. Committed (`898b1d1`), pushed.
**The spec's `Breakdown-ready: true` header is now stale** — it was set
when the critic approved the OLD (R1-R4-only) version; R5-R8 haven't been
critiqued. Existing task 01 (`tasks/01-token-discipline-bullets.md`,
`Status: pending`) covers only R1-R4. Next step: re-run `/critique` on this
spec, then decide (per the spec's own Open questions) whether R5-R8 fold
into task 01 or become a new task 02.

**Housekeeping this session** (both already committed/pushed):

- Relocated a misfiled cross-repo `HANDOFF.md` (about an unrelated
  `human-tasks` walkthrough) from this repo's tracked tree to
  `~/.claude/HANDOFF.md` (global, untracked) — commit `0517569`.
- Found the installed Claude Code plugin cache
  (`~/.claude/plugins/cache/agentic-toolkit/agentic/0.8.56/`) is stale
  vs. this repo's dev HEAD (now 0.9.0 after this run's version bump).
  **Run `bin/refresh-plugins` once 0.9.0 is confirmed on the remote** — it
  re-syncs the marketplace, reinstalls, and prunes stale cached versions.

## Gotchas

- **Always resolve skills to THIS repo's own `.claude/skills/<name>/` files,
  never the cached plugin path** — the cache lags behind dev HEAD (0.8.56
  vs 0.9.0 this run) and drain's own SKILL.md/reference.md changed
  substantively mid-run (drain-readiness gate replaced the old
  attended/classification-gate language; see `[[feedback_no_attended_tasks]]`
  memory). Diff the two before trusting either if unsure.
- The "over wake budget" hook fires on THIS session's own main-loop context
  size, not subagents' — dispatched workers/drain generations run in
  isolated contexts that get discarded; only their ≤2k-token verdicts land
  in the parent's transcript. What actually bloated this session: full
  SKILL.md/reference.md reads (repeated), every git/bash diagnostic output,
  ~9 subagent verdicts, and a 69-item workboard JSON summary printed
  inline. A fresh session should delegate the workboard scan-and-summarize
  step to a scout (per the new R5/R6 in `context-blowout-subagent-guards`)
  rather than repeating that mistake.
- Global CLAUDE.md / rules files were spot-checked this session and look
  appropriately scoped (all within the repo's own SKILL.md ≤500-line /
  "cite don't restate" conventions) — no bloat found there; the actual
  problem was workboard's per-invocation relay step, not the always-loaded
  config files.
- Two other live sessions (`claude-b7`, `claude-9a`) shared this checkout
  earlier in the session with no observed collision (owner-lease + CAS-flip
  machinery held). Re-check `claude agents --json` before heavy multi-file
  work.

## Verification

- All project gates (`tests/test_*.sh`, `claude plugin validate .`,
  `bash evals/lint-ultra-gate.sh`, `./bin/check-agent-model-pins`,
  `./evals/runner-selftest.sh`, `./specs/status.sh`) were green after every
  merge this session, most recently after `skill-doc-size-guards` task 05.
- The amended SPEC.md has not been re-critiqued — do that before any
  further breakdown of `context-blowout-subagent-guards`.
- Workboard UX/accuracy testing (Steven's most recent ask) has NOT started
  — no browser session opened yet, no agent-console frontend files read.

## Next step

1. Check on the drain queue (`bash specs/status.sh`, `git log --oneline -5`)
   — it may have finished or batoned further since this handoff was
   written. Do not restart or duplicate it; only observe.
2. Re-critique `specs/context-blowout-subagent-guards/SPEC.md` (now
   R1-R8), then decide the task 01 vs. new-task-02 split per its Open
   questions, then `/breakdown` and eventually `/drain` it.
3. Pick up the workboard UX/accuracy testing task: load
   `mcp__claude-in-chrome__*` tools, screenshot
   `http://127.0.0.1:8899/workboard`, cross-check rendered data against
   `python3 .claude/skills/workboard/workboard.py --json` (run via a scout,
   not inline, per the new R6 above — eat your own dog food), and apply
   `frontend-design`/`dataviz` skill guidance for any readability fixes to
   `agent-console`'s workboard rendering code.
