Run-token: e83f34f07094a4fa
Generation: 5
Spec: specs/prose-review
Breakdown-failed:
Intake-failed: specs/build-doc-currency-check, specs/codequality-agent-console-mutation-coverage, specs/codequality-antigravity-content-parity, specs/codequality-shared-header-parsing, specs/domain-knowledge-base, specs/idea-research-freshness
Stub-intake-failed:

## Done / next

Gen 4 recorded 5 units (W=1 budget 5) as critique-intake attempts and batoned.
All 5 came back NOT READY — findings written to each spec's critique-findings.md,
each lease claimed transiently then released, each spec added to Intake-failed:

- codequality-agent-console-mutation-coverage → NOT READY (6 findings): spec
  factually mischaracterizes execute_push (no dirty-check/commit/ahead-behind;
  `:2872` is set_priority's line), resume_agent "empty prompt" is not a failure
  case, render_markdown has zero acceptance criteria. Needs human spec revision.
- codequality-antigravity-content-parity → NOT READY (3 findings): the
  "every other mirrored .py is byte-identical" premise is FALSE — 3 legitimately
  ported .py files diverge, so the all-.py byte-parity gate is a false-positive
  machine that can never go green and would red-bar the repo's whole check loop.
  (Real drift it targets IS present: _shared/test_viz.py 210 vs mirror 198.)
- codequality-shared-header-parsing → NOT READY (3 findings): criterion #5
  (`diff -r` empty vs mirror) unsatisfiable — prioritize_scan.py legitimately
  diverges from its mirror; loader bootstrap ambiguous; "share the regex" silently
  widens prioritize's parsing from P[0-3] to any digit. Refactor IS worth doing.
- domain-knowledge-base → NOT READY (5 findings): core criteria gate on
  deep-research/Workflow dispatch + live interactive /idea runs a drain worker
  can't do (no manual-pending path); depends on unbuilt sibling
  idea-research-freshness shipping first.
- idea-research-freshness → NOT READY (6 findings): ships freshness fixtures but
  NO deterministic checker over them (its core deliverable); criteria gate on
  running /idea end-to-end; inserting a step breaks ~12 internal `step N`
  cross-refs. R7/R8/R9 authoring conventions ARE pinned. Ship before
  domain-knowledge-base (that sibling defers the `Verified:` convention here).

PATTERN for the human: all three codequality-* specs (from the 2026-07-10 batch)
are NOT READY, two sharing the same false byte-parity-vs-antigravity-mirror
premise — the port is "near-identical," not byte-identical, so any spec whose
gate is `diff -r`/`diff -q` empty against the mirror is a false-positive machine.

prose-review remains FULLY GATED on 03's deferred answer (still deferred, no
## Answers). 04 depends on 01+03; retrofits 05-13 depend on 03. Lease HELD at
gen 5. Gen 5 continues the EXHAUSTION PHASE:

1. Critique intake, one spec per pass, at most once per spec per run, skipping the
   6 Intake-failed specs above. Remaining eligible (order = Priority then path):
   large-codebase-context-guide, model-routing-multi-vendor-citations,
   narrow-autopilot, retire-static-dashboards, rigor-tier, trajectory-evals,
   workboard-auto-triage (all P2), then first-pass-success-rate (P3),
   harness-audit (P3). Per spec: scout sanity-check (already built? archive beats
   critique), claim lease transiently, /critique via Skill tool, route
   READY → 3b same session / NOT READY → write critique-findings.md + add to
   Intake-failed + release lease.
2. Stub intake (screen script .claude/skills/drain/screen-stub.sh FIRST per stub):
   agent-tier-leaks/tasks/04,05; drain-wake-cost/tasks/04;
   orchestrator-share-audit/tasks/03; spec-completion-review/tasks/04,05.
   Note on scr/05 (build-mirror gap): gen 2 flagged it needs a human Touch
   amendment or new task — likely DECISION-SHAPED or refused.
3. 3b auto-breakdown for any Breakdown-ready:true spec without tasks/ (none yet).
4. Batch interview LAST (only when 1-3 all come up empty): the prose-review 03
   deferred question (verbatim in that task file under ## Deferred questions;
   options a/b/c, option (a) = amend Touch to include vale/.vale.ini.template +
   central Google.EmDash disable, matches attempt 1's working discarded impl) +
   exit checklist. A headless generation reaching it writes questions into this
   baton and stops.

When 03's answer lands and flips it pending: re-dispatch 03 (prose-review lease
held), then 04 (mirror+bump closing; bumps plugin.json relative to its own base,
plugin.json currently 0.8.48), then retrofits 05-13 — W=3 authorized for the
retrofit group ONLY (Group: 05..13, pairwise-disjoint Touch; budget then drops to
max(2,6-3)=3 units/gen). Retrofits are CROSS-REPO (worktree the TARGET repo per
docs/memory/drain-dispatch-lessons.md); each has a MANDATORY CI paths-ignore
precondition; task 09 (portfolio-tracker) AUTO-PUSHES/AUTO-DEPLOYS on commit —
BLOCK rather than commit if its precondition fails.

## Anomalies / carry-forward

- SPEC-COMPLETION REVIEW OBLIGATION: prose-review had tasks 01+02 complete DONE
  earlier this run, so when it eventually reaches nothing-left-to-dispatch and its
  lease releases, the spec-completion review step (drain SKILL.md) MUST run first
  (evidence file specs/prose-review/evidence/spec-review.md is the idempotency
  token — not yet written). Do NOT retro-apply the review to specs drained before
  the machinery merged (cache-reprime, agentprof-attr, drain-forward-progress,
  spec-completion-review itself).
- vale side effect: any worker that runs bin/install-vale inside its worktree
  repoints the machine-global ~/.vale.ini StylesPath at that worktree; after
  merging/discarding such a branch, re-run `bash bin/install-vale --force` from
  /Users/sjaconette/claude and confirm `grep '^StylesPath' ~/.vale.ini` shows
  /Users/sjaconette/claude/vale/styles.
- Two FOREIGN owner leases live and untouchable: specs/draft-auto-promotion/,
  specs/work-exhaustion/. Never touch specs/agentprof-antigravity-adapter.
- Foreign worktrees/branches live in the shared checkout (task/01-verifier-leak-trace,
  task/02-namespace-attribution, task/03-closing-gate, task/03-ship-gate) — other
  sessions' work; never sweep them.
- Untracked slack-relay/ dir in the main checkout belongs to another session.
- plugin.json at 0.8.48; prose-review/04 closing task bumps relative to its own base.
- Generations cap = 10 (this baton hands to gen 5).
