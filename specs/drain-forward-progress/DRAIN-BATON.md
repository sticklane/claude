Run-token: e83f34f07094a4fa
Generation: 4
Spec: specs/prose-review
Breakdown-failed:
Intake-failed: specs/build-doc-currency-check
Stub-intake-failed:

## Done / next

Gen 3 recorded 5 units (W=1 budget 5) and batoned:
- prose-review/tasks/01-skill-and-doctrine — DONE, merged f3e11d7 (skill + reference + CLAUDE.md pointer; 2 decisions logged on task file)
- prose-review/tasks/02-vale-install — DONE, merged 9f16219 (bin/install-vale, vale/ config, .gitignore; discovery recorded RESOLVED: drain re-ran `bash bin/install-vale --force` from main checkout post-merge)
- prose-review/tasks/03-gate-stanza-selfapply — attempt 1 (opus) DONE but MERGE-FAILED on R4 Touch enforcement (changed vale/.vale.ini.template, outside Touch); relaunch (fable) returned DEFERRED: C2 (`vale README.md AGENTS.md` exit 0) is unsatisfiable within Touch — Google.EmDash (existence rule, no vocab suppression) fires 22x on the deliberate house spaced-em-dash style. Status: deferred; exact question on the task file under ## Deferred questions (options a/b/c; option (a) = amend Touch to include vale/.vale.ini.template + central EmDash disable, matches attempt 1's working implementation).
- Critique intake #1: specs/build-doc-currency-check → NOT READY (4 findings recorded at specs/build-doc-currency-check/critique-findings.md; lease released; on Intake-failed line above).

prose-review is now FULLY GATED on 03's deferred answer: 04 depends on 01+03; retrofits 05-13 depend on 03. Nothing dispatchable anywhere in scope — gen 4 continues the EXHAUSTION PHASE:

1. Critique intake, one spec per pass, at most once per spec per run. Eligible
   (all P2 unless noted, order = Priority then path; skip any on Intake-failed):
   codequality-agent-console-mutation-coverage, codequality-antigravity-content-parity,
   codequality-shared-header-parsing, domain-knowledge-base, idea-research-freshness,
   large-codebase-context-guide, model-routing-multi-vendor-citations, narrow-autopilot,
   retire-static-dashboards, rigor-tier, trajectory-evals, workboard-auto-triage,
   first-pass-success-rate (P3), harness-audit (P3).
   READY → 3b auto-breakdown same session → dispatch its tasks.
2. Stub intake (screen script .claude/skills/drain/screen-stub.sh FIRST per stub):
   agent-tier-leaks/tasks/04,05; drain-wake-cost/tasks/04;
   orchestrator-share-audit/tasks/03; spec-completion-review/tasks/04,05.
   Note on scr/05 (build-mirror gap): gen 2 flagged it needs a human Touch
   amendment or new task — likely DECISION-SHAPED or refused.
3. 3b auto-breakdown for any Breakdown-ready:true spec without tasks/ (none yet).
4. Batch interview LAST (only when 1-3 all come up empty): the prose-review 03
   question above + exit checklist. A headless generation reaching it writes
   questions into this baton and stops.

When 03's answer lands and flips it pending: re-dispatch 03 (prose-review lease
is already held by this run), then 04, then retrofits 05-13 — W=3 authorized for
the retrofit group ONLY (Group: 05..13, pairwise-disjoint Touch; budget then
max(2,6-3)=3 units/gen). Retrofits are CROSS-REPO (worktree the TARGET repo per
docs/memory/drain-dispatch-lessons.md); each has a MANDATORY CI paths-ignore
precondition; task 09 (portfolio-tracker) AUTO-PUSHES/AUTO-DEPLOYS on commit —
BLOCK rather than commit if its precondition fails.

## Anomalies / carry-forward

- SPEC-COMPLETION REVIEW OBLIGATION: prose-review had tasks 01+02 complete DONE
  this run, so when it eventually reaches nothing-left-to-dispatch and its lease
  releases, the spec-completion review step (drain SKILL.md) MUST run first
  (evidence file specs/prose-review/evidence/spec-review.md is the idempotency
  token — not yet written). Do NOT retro-apply the review to specs drained
  before the machinery merged (cache-reprime, agentprof-attr,
  drain-forward-progress, spec-completion-review itself).
- vale side effect: any worker that runs bin/install-vale inside its worktree
  repoints the machine-global ~/.vale.ini StylesPath at that worktree; after
  merging such a branch, re-run `bash bin/install-vale --force` from
  /Users/sjaconette/claude (happened twice in gen 3; fixed both times).
- Two FOREIGN owner leases live and untouchable: specs/draft-auto-promotion/,
  specs/work-exhaustion/. Never touch specs/agentprof-antigravity-adapter.
- Foreign worktrees/branches live in the shared checkout (task/01-verifier-leak-trace,
  task/02-namespace-attribution, task/03-closing-gate, task/03-ship-gate) — other
  sessions' work; never sweep them.
- Untracked slack-relay/ dir in the main checkout belongs to another session.
- plugin.json at 0.8.48; prose-review/04 closing task bumps relative to its own base.
- Generations cap = 10 (this baton hands to gen 4).
