Run-token: e83f34f07094a4fa
Generation: 3
Spec: specs/prose-review
Breakdown-failed:
Intake-failed:
Stub-intake-failed:

## Done / next

Gen 2 recorded 4 verdicts (all DONE, all merged + pushed) and batoned at the
clean spec-completion-review boundary (within the W=1 budget of 5):
- drain-forward-progress/tasks/03-mirror-bump — DONE, merged (dfp fully drained, lease released); codex-wrapper-update decision logged, ultra-gate green
- spec-completion-review/tasks/01-drain-step — DONE, merged; ultra-gate green; discovery materialized (flip-message format transition, stub 04)
- spec-completion-review/tasks/02-build-parity — DONE, merged; ultra-gate green; discovery materialized (build-mirror gap, stub 05)
- spec-completion-review/tasks/03-mirror-bump — DONE, merged (scr fully drained, lease released); soft-reset decision logged; plugin.json now 0.8.48

The spec-completion-review machinery is now MERGED (SKILL.md carries a
"## Spec-completion review" step; build SKILL.md carries the bare-SPEC
parity sentence). Gen 3 loads the UPDATED drain SKILL.md fresh, so it applies
that step naturally. Per the human's standing instruction: do NOT retro-apply
it to specs drained before it merged (cache-reprime, agentprof-attr, dfp,
AND spec-completion-review itself — scr built the machinery, it is not a
"drained-after" spec). Apply it to prose-review and later.

NEXT (gen 3): drain specs/prose-review (13 tasks). Per its SPEC Parallelization:
- Group: 01, 02 (co-admissible); at W=1 run serially, 01 then 02.
- 03 after 01 AND 02 (closing-ish for the core).
- 04 after 01 AND 03 (mirror+bump closing — bumps plugin.json relative to base).
- Retrofit tasks 05-13 after 03: Group: 05..13 (pairwise-disjoint Touch).
  You MAY run W=3 for the retrofit group only (explicit throughput authorization
  in the human's standing chain; baton budget then = max(2,6-3) = 3 verdicts/gen).
VERIFY the exact dependency/group lines against specs/prose-review/SPEC.md and
each task header at inventory — the above is from the baton map, re-read to confirm.

## Anomalies / carry-forward

- prose-review retrofits 05-13 have CROSS-REPO Touch (other repos on this machine).
  Follow docs/memory/drain-dispatch-lessons.md cross-repo procedure (worktree the
  TARGET repo too, not just this one). Each retrofit carries a MANDATORY CI
  paths-ignore precondition before committing in the target repo.
  Task 09 (portfolio-tracker) AUTO-PUSHES/AUTO-DEPLOYS on commit — if its
  paths-ignore precondition fails, BLOCK the task rather than commit.
- Draft stubs created by gen 2 (for final-exhaustion stub intake / exit checklist):
  - specs/spec-completion-review/tasks/04-flip-message-format-transition.md (Blocking: no)
  - specs/spec-completion-review/tasks/05-build-mirror-gap.md (Blocking: no) — the
    build SKILL.md spec-completion sentence ships un-mirrored to antigravity/codex
    build ports; needs a human Touch amendment or new task (drain can't edit Touch).
  Pre-existing drafts also in scope at exhaustion: agent-tier-leaks/04,05;
  drain-wake-cost/04; orchestrator-share-audit/03.
- Two FOREIGN owner leases live and untouchable: specs/draft-auto-promotion/DRAIN-OWNER.md,
  specs/work-exhaustion/DRAIN-OWNER.md. Never touch specs/agentprof-antigravity-adapter.
- Baton budget: W=1 → 5 verdicts/gen; W=3 (retrofit window) → 3 verdicts/gen.
- Generations cap = 10 (currently gen 3). plugin.json at 0.8.48; prose-review/04
  closing task bumps relative to its own base.
