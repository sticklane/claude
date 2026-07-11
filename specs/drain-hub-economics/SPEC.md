# Drain gen-1 hub-economics advisories

Status: open
Priority: P1
Breakdown-ready: true

## Problem

The wake-economics doctrine shipped in specs/drain-wake-cost tells drain
hubs to stay small and run on the deep tier or below ("a frontier hub
model roughly doubles wake cost for no quality gain" — drain SKILL.md,
Wake economics). But nothing *checks* either condition at launch, and the
first post-fix drain run violated both invisibly: the 2026-07-11 run
launched inside an existing frontier-model (fable) analysis session whose
main-loop context was already p50 203k / p90 261k tokens per call — every
worker-verdict wake re-primes that context at the 1.25× cache-write rate
(~$3-5/wake at that size vs ~$0.75 at 40k; see
specs/cache-reprime-visibility/EVIDENCE.md and
specs/drain-wake-cost/EVIDENCE.md). The doctrine exists; the launch-time
mirror to hold it up to does not.

Both signals are cheap to read at gen-1 startup in the Claude Code
runtime: the session's own model is disclosed to it in its system context
(the harness states the powering model by name; runtimes/ maps names to
tiers), and "this session is already heavy" is observable from the
conversation shape (the drain launch arriving beyond the session's first
few turns) even without a context-size API. Runtimes that do not disclose
the session model in-session simply skip the R1 advisory.

## Solution

Two advisory lines in drain's gen-1 startup (SKILL.md step 1, beside the
shell-naming and session-sweep steps), attended-mode aware: warn on a
frontier-tier hub, and warn when the hub session visibly carries heavy
unrelated prior context — each recommending the cheap fix (relaunch the
drain in a fresh deep-tier session; the committed queue state makes that
free). Advisories only — never block dispatch; an explicitly authorized
run proceeds after printing them.

## Requirements

- R1 **Frontier-hub advisory.** At gen-1 startup, when the hub session's
  own model is frontier-tier (signal: the model name the harness disclosed
  to the session in its system context, mapped through runtimes/ tier
  language; Claude default frontier = fable — where the runtime discloses
  no model, skip this advisory), drain prints one advisory
  line in the plan report citing the wake-economics doctrine and
  recommending a deep-tier (opus) or lower hub, with the exact relaunch
  shape (fresh session, same /drain argument — queue state is committed,
  nothing is lost). The skill text titles this block "Hub-economics
  advisory" (the acceptance greps key on that literal). Never printed on
  baton generations (the lineage is already running) and never blocking.
- R2 **Heavy-hub advisory.** At gen-1 startup, when the session visibly
  carries substantial prior unrelated work (heuristic, stated in the
  skill text: the drain launch is not within the session's first few
  turns — no context-size API exists, so the turn-count shape is the
  signal), drain prints one advisory recommending a fresh session
  relaunch, same shape as R1. Advisory only.
- R3 **Mirror + plugin hygiene.** The SKILL.md change mirrors to
  antigravity's drain workflow as a content-equivalent note (paraphrased
  port — content-coverage check, not byte-diff; see
  docs/memory/workboard-mirror-verbatim.md) and ships with a
  `.claude-plugin/plugin.json` bump in the closing commit;
  `claude plugin validate .` passes.

## Out of scope

- Blocking or auto-relaunching (advisory only; the human decides).
- Baton-trigger changes, context-size instrumentation (drain-wake-cost
  and cache-reprime-visibility own those).
- Any harness API for reading context size or model programmatically —
  the skill text states the signals the session can already observe.

## Acceptance criteria

- [ ] `grep -qi 'hub-economics advisory' .claude/skills/drain/SKILL.md`
  hits (the phrase is absent from the file today — verified 2026-07-11 —
  so this cannot pass vacuously) AND MANUAL: the block recommends a
  deep-tier fresh-session relaunch, applies only to gen 1, and is
  explicitly non-blocking (R1)
- [ ] MANUAL: the heavy-hub advisory names its observable heuristic (drain
  launched beyond the session's first few turns) and the same relaunch
  recommendation (R2)
- [ ] `grep -qi 'hub-economics advisory' antigravity/.agents/workflows/drain.md`
  hits (phrase absent today; content-coverage, not byte-diff) AND
  `claude plugin validate .` passes AND the closing task's own commit
  modifies the plugin version line:
  `git show <closing-commit> -- .claude-plugin/plugin.json | grep -q '^+.*"version"'`
  where `<closing-commit>` = HEAD immediately after the closing commit
  lands (the verifier resolves it; /breakdown may substitute the SHA)
  (immune to a sibling spec bumping the same file earlier in the run).
  The literal block title "Hub-economics advisory" appears in BOTH files —
  the antigravity port may paraphrase the body but keeps the title
  literal (that is what its grep keys on) (R3)

## Open questions

- None. (R2's "first few turns" is deliberately a prose heuristic — the
  skill text owns the wording; pinning a number would false-fire on
  legitimate multi-turn drain prep.)

## Parallelization

Task map: 01 = R1+R2 (drain SKILL.md block); 02 = R3 closing gate
(antigravity port + plugin bump), depends on 01. Serialized — no Group
lines (format grammar per specs/drain-rolling-window/SPEC.md's
Parallelization section).
