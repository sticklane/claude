# HANDOFF: /drain whole-queue run — generation-3 hub refresh

Note: `.claude/HANDOFF.md` is already occupied by an unrelated session's
handoff (human-tasks/ynab-triage-skill work) — this file uses a distinct
name to avoid clobbering it. Do not delete or edit `.claude/HANDOFF.md`;
it belongs to a different task.

## Task

A `/drain` run with no spec argument (whole `specs/` queue in scope),
launched by the user in this conversation ("drain everything", then a
second explicit `/drain` re-invocation, then "continue"). This session was
the generation-1 interactive hub. It hit its wake budget twice (3 then 4
cache re-primes, ~285k p90 context) and batoned twice:
gen1 → gen2 (agentId no longer relevant, already completed) → gen3
(background agent, id `a6dc129243c9ce2ad`, **still running as of this
handoff** — do not spawn a duplicate generation-3 agent).

## State

Landed and merged to `origin/main` (verified via drain's own merge-time
gates, not re-verified here — see each spec's `evidence/spec-review.md`
committed alongside):

- `human-blocker-impact-clarity` — 4/4 tasks done, lease released
- `prompt-tweaking-roi` — 1/1 task done, lease released
- `drain-frontier-scanner` — 4/4 non-draft tasks done (05 left as draft
  stub), lease released
- `drain-session-naming-always-propose` — done, lease released
- `drain-multi-spec-swarm` — partial (task 05 done this run before gen 2's
  baton; task 02 still open), lease held under Run-token
  `6da9bf9a672dfa74`
- `eval-coverage-tiers` — partial (task 03 done; tasks 04-08 still open),
  same lease

Reclaimed: the 3-spec lease originally held by an abandoned "vm"-hosted
run (Run-token `6da9bf9a672dfa74` itself, actually — gen 2 adopted that
exact token when it confirmed the run dead and reclaimed it, rather than
minting a new one, per the Reclaim procedure).

Currently in flight: generation 3 (agent `a6dc129243c9ce2ad`) adopting
`specs/drain-multi-spec-swarm/DRAIN-BATON.md`, working: finish
drain-multi-spec-swarm/02, finish eval-coverage-tiers/04-08,
spec-completion review + release both leases, then critique intake
(`drain-plugin-path-resolution`), 3b auto-breakdown
(`drain-read-once-discipline`), then stub intake on ~9 draft stubs.

## Exact next step for the resuming session

1. Check for a live notification from agent `a6dc129243c9ce2ad` first —
   if the harness already delivered one, read it before doing anything
   else; don't re-derive what it already reported.
2. If it batoned again (generation 4): find the newest
   `specs/*/DRAIN-BATON.md` by commit time (`git log -1 --format=%cI -- '
specs/*/DRAIN-BATON.md'` per candidate, or just check whichever spec(s)
   still carry a `DRAIN-OWNER.md` under Run-token `6da9bf9a672dfa74`),
   read it, and spawn generation 4 the same way generation 3 was spawned:
   `Agent` tool, `subagent_type: "claude"`, `run_in_background: true`, a
   self-contained prompt telling it to adopt the baton, follow
   `.claude/skills/drain/SKILL.md`, reuse
   `.claude/worktrees/drain-orchestrator`, emit `agentprof` stage markers,
   keep going per the R1 exhaustion contract, and baton again itself at
   its own threshold rather than running the resuming session's context
   up. Then end that turn immediately (one-writer invariant) — don't keep
   the resuming session as the active queue-writer either.
3. If it reached step 4 (batch interview + seven-section exit checklist):
   the run is done — relay the checklist to the user, no further spawning
   needed.

## Files touched (this hub session, generations 1-2 directly; generation

3's own changes are not yet known to this file)

- `.claude/rules/human-blockers.md`, `.claude/skills/drain/reference.md`,
  `HUMAN.md`, `antigravity/.agents/workflows/drain.md`,
  `.claude-plugin/plugin.json` (`human-blocker-impact-clarity`'s 4 tasks)
- `.claude/rules/token-discipline.md` (`prompt-tweaking-roi`'s 1 task)
- Per-spec `DRAIN-OWNER.md` / `DRAIN-BATON.md` / `evidence/spec-review.md`
  files across the specs listed above (queue-state bookkeeping)

## Gotchas

- `drain_frontier.py` exits 2 on any spec dir containing a `Status: draft`
  or `Status: obsolete` task file ("malformed Status value") — confirmed
  on 11 specs. Fall back to verbatim header reads there per SKILL.md's own
  contract; it is NOT a real failure to route around differently.
- Task-file merges conflict on `Status: in-progress` vs `Status: done`
  essentially every time (the orchestrator's own flip commit vs. the
  worker's own close-out commit touching the same line) — always resolve
  to `done`, it's mechanical.
- A repo formatter/linter hook fires on Edit/Write of task and evidence
  files — re-read before a follow-up Edit whose `old_string` targets a
  just-reformatted region; it mangled a conflict-marker remnant into
  escaped/broken text once this run (`prompt-tweaking-roi/01`'s task
  file), needing a manual rewrite.
- At least one implementation-worker skipped its own task file's
  Status/checkbox close-out, misreading its `Touch:` header as excluding
  the task file itself (`human-blocker-impact-clarity/04`) — drain had to
  apply that close-out itself post-merge after independently re-verifying
  the acceptance commands. Watch for this pattern recurring; may be worth
  tightening the worker-prompt wording if it does.
- Another live local Claude Code session (name `claude-9d` in
  `claude agents --json`, cwd also `/Users/sjaconette/claude`) shares this
  repo but works on unrelated tasks (it wrote the pre-existing
  `.claude/HANDOFF.md` this file deliberately did not touch) — not a
  drain collision, just noise if you check live sessions.
- `agentprof:stage=*` / `agentprof:role=*` HTML-comment markers were
  missed for this hub's first 5 verdicts before the human caught it —
  emit them from the very first step in any successor generation.

## Verification

No task from this hub session is unverified-and-parked: every `done` task
listed above already passed drain's own merge-time whitelist-diff check
plus project gates (`tests/test_*.sh`, `evals/lint-ultra-gate.sh`) before
merging — that IS this run's verification layer, already applied per
task, not a separate pass owed here. Two items are explicitly
manual-pending (not blocking, both self-assessed compliant by their
worker, awaiting a human/reviewer read): `prompt-tweaking-roi/01`'s R2/R4
citation check, and `human-blocker-impact-clarity/03`'s end-to-end
readability check.
