Run-token: c36d516ab2c632d6
Generation: 3
Spec: specs/agentprof-attribution-gaps
Breakdown-failed:
Intake-failed:
Stub-intake-failed:

## Done / next

Gen 2 recorded 5 verdicts (all DONE+merged+pushed):
- workflow-model-pins: 02 (workflow-author stage-tiering rule), 03 (plugin bump
  0.8.40→0.8.41 + validate). Spec FULLY done; lease RELEASED.
- agentprof-attribution-gaps: 01 (skill-frame fallback from <command-name>),
  02 (project normalization (home)/(tmp)/agent-dir fold; 2 reversible decisions
  recorded in task file), 03 (pending-sample consolidation + Options.KeepPending;
  2 discovery stubs 07/08 created; 2 manual-pending measurements flagged).

Lease HELD by this run: specs/agentprof-attribution-gaps/DRAIN-OWNER.md
(Generation now 3 — adopt it, do NOT re-mint the token).

Next dispatch order (W=1, one at a time):
- agentprof-attribution-gaps: 04 (agent-instance-label — serial chain
  continuation on internal/claude/claude.go, depends on 03 which is done),
  then 05 (tools-bucket — parallel-safe vs chain head but W=1 so still alone),
  then 06 (frame-denylist — LAST). Drafts 07/08 exist (Status: draft) → stub
  intake at exhaustion.
- Then drain-hub-economics (01 startup-advisories → 02 mirror-and-bump); claim
  its lease when its dispatch begins, release agentprof-attribution-gaps first.
- Then agent-efficiency-guards (01 skill-text-guards → 02 mirror-and-bump).

## Anomalies

- W=1 throughout (no Parallel-window headers).
- ag chain 04 edits the SAME file internal/claude/claude.go — never parallel;
  06 runs last.
- aeg/01 touches drain/critique SKILL.md (ultra-path skills): its worker MUST
  run `bash evals/lint-ultra-gate.sh` before committing — add that line to that
  worker's prompt.
- aeg/02 AND dhe/02 each bump .claude-plugin/plugin.json — bump RELATIVE to the
  value at the task's own base, NEVER a pinned literal. Plugin was 0.8.42 on
  origin at gen-2 handoff (foreign session bumped it past my 0.8.41); expect it
  to move.
- FOREIGN live session c2cec1dd draining specs/agentprof-antigravity-adapter in
  this same checkout. Leases keep specs disjoint. Expect upstream movement:
  fetch + ff/rebase before each lease claim AND retry a rejected push by
  rebasing your LINEAR flip commit onto origin/main (this happened once at
  gen 2's ag/03 flip — non-fast-forward, resolved by fetch+rebase, no conflict;
  foreign commits are path-disjoint). NEVER touch specs/agentprof-antigravity-adapter
  or specs/antigravity-mirror-broken-refs.
- ag/03 left TWO manual-pending measurements (14-day-window ≥8% sample drop +
  Agent-tool/TaskOutput shape investigation) — need $HOME/.claude transcript
  data unreachable from an isolated worktree; runnable commands recorded in
  specs/agentprof-attribution-gaps/evidence/03-pending-volume.md. Surface both
  on the exit checklist for a human/orchestrator to run post-merge.
- Untracked slack-relay/ dir sits in the checkout — NOT ours; never stage,
  commit, or touch it (path-scoped commits only).
- Worker branch naming: workers commit either to task/NN-<slug> OR to their
  auto worktree-agent-<hex> branch — check both before computing merge-base.
- Commit EVERY queue-state/spec edit IMMEDIATELY, path-scoped; run the drain
  hub on opus tier or below; never pull code diffs/test output inline (scouts).
