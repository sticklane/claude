Run-token: e83f34f07094a4fa
Generation: 2
Spec: specs/drain-forward-progress
Breakdown-failed:
Intake-failed:
Stub-intake-failed:

## Done / next

Gen 1 recorded 5 verdicts (all DONE, all merged + pushed):
- cache-reprime-visibility/tasks/05 (SCHEMA.md overview) — DONE, merged, lease released (spec fully drained)
- agentprof-attribution-gaps/tasks/07 (--keep-pending CLI) — DONE, merged; reversible decision logged
- agentprof-attribution-gaps/tasks/08 (meta/sidechain pending match) — DONE, merged; decision + manual-pending note logged; lease released (spec fully drained)
- drain-forward-progress/tasks/01 (intake contract R1/R3/R4) — DONE, merged, ultra-gate green
- drain-forward-progress/tasks/02 (screen-stub abspath rule fix R2) — DONE, merged, fixtures+ultra-gate green; reversible decision logged

NEXT (gen 2): drain-forward-progress/tasks/03-mirror-bump (closing task R4+R5;
deps 01,02 both done → dispatchable NOW). Touch: antigravity/.agents/workflows/drain.md,
codex/.agents/skills/drain/SKILL.md, .claude-plugin/plugin.json. It is the mirror+bump
closing task and is ULTRA-PATH-adjacent (codex drain SKILL.md) — its worker must run
`bash evals/lint-ultra-gate.sh` before committing. drain-forward-progress MUST fully
complete and merge (incl. 03) BEFORE any spec-completion-review task dispatches (both
specs edit drain SKILL.md/reference.md).

Then: spec-completion-review (01,02 group per SPEC, 03 closing) → prose-review
(01,02 group, 03 after both, 04 after 01+03, retrofits 05-13 after 03 with W=3 allowed).

## Anomalies

- prose-review retrofits 05-13 have CROSS-REPO Touch (other repos on this machine);
  follow docs/memory/drain-dispatch-lessons.md cross-repo procedure (worktree the target
  repo too); each carries a mandatory CI paths-ignore precondition before committing in
  the target repo; task 09 (portfolio-tracker) auto-pushes/auto-deploys on commit — if
  its precondition fails, BLOCK rather than commit.
- If spec-completion-review machinery lands, it adds a spec-review step; do NOT
  retro-apply it to specs drained before it merged (cache-reprime, agentprof-attr, dfp).
- Two FOREIGN owner leases live and untouched: specs/draft-auto-promotion/DRAIN-OWNER.md,
  specs/work-exhaustion/DRAIN-OWNER.md — not in scope, leave alone.
- Baton budget: W=1 → 5 verdicts per generation (max(2,6-W)); W=3 during retrofit group → 3.
- Generations cap = 10.
