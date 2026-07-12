Run-token: e83f34f07094a4fa
Generation: 6
Spec: specs/prose-review
Breakdown-failed:
Intake-failed: specs/build-doc-currency-check, specs/codequality-agent-console-mutation-coverage, specs/codequality-antigravity-content-parity, specs/codequality-shared-header-parsing, specs/domain-knowledge-base, specs/idea-research-freshness, specs/narrow-autopilot
Stub-intake-failed:

## Done / next

Gen 5 recorded 5 units (W=1 budget 5) and batoned. Work this gen — all inline
(this environment exposes NO agent-dispatch/Task tool; see Anomalies):

1. critique-intake large-codebase-context-guide → READY. All mechanical gate
   anchors verified present (tests/test_doc_links.sh enforces the mermaid
   fence; token-discipline "Delegation defaults" section present; existing
   guides establish the pattern). Deps conditional (idea-research-freshness
   `Verified:` "if landed"), not hard. Wrote Breakdown-ready: true.
2. auto-breakdown large-codebase-context-guide → 1 task: task 01 (guide +
   token-discipline bullet), Status: pending, Depends on: none — DISPATCHABLE.
   No antigravity mirror needed (.claude/rules/ and docs/guides/ aren't
   mirrored — verified). Lease released.
3. critique-intake model-routing-multi-vendor-citations → READY. All quotes
   and URLs supplied verbatim in the spec; insertion anchor
   "## Rules and skills this page explains" present (line 71); "Cross-vendor
   grounding" absent. Minor: AC6 references absent .claude/runtime.md
   (vacuously satisfied). Wrote Breakdown-ready: true.
4. auto-breakdown model-routing-multi-vendor-citations → 1 task: task 01
   (add ## Cross-vendor grounding section), Status: pending — DISPATCHABLE.
   Lease released.
5. critique-intake narrow-autopilot → NOT READY (6 findings in
   specs/narrow-autopilot/critique-findings.md). Added to Intake-failed.
   High-blast-radius skill-retirement (deletes /autopilot, edits ultra-path
   build/SKILL.md + drain/reference.md, whole-repo sweep, plugin bump). Key
   findings: R6/AC7 grep `grep -rln '\bautopilot\b' .claude/ ...` returns 887
   files (only 19 tracked; ~868 are transient .claude/worktrees/*) — scope it
   to `git grep -ln` so it's deterministic; line anchors drifted
   (drain/reference.md:388→:776, onboard:74→:79); AC2 verbatim-check not
   runnable; no ultra-gate AC; R7 antigravity fold underspecified (no
   antigravity autopilot mirror exists); live sequencing dep on
   build-doc-currency-check (itself NOT READY).

DISPATCHABLE WORK NOW EXISTS for gen 6 (was empty at gen 5 start):
- specs/large-codebase-context-guide/tasks/01-write-guide-and-rule-bullet.md
  (pending, Depends on: none)
- specs/model-routing-multi-vendor-citations/tasks/01-add-cross-vendor-grounding-section.md
  (pending, Depends on: none)
Both are P2 single-task doc deliverables, gated on tests/test_doc_links.sh +
grep ACs, each with one manual-pending human URL/readability criterion. Gen 6
dispatches these (W=1) BEFORE any further critique/stub intake — dispatch
outranks exhaustion-phase work. BUT only a generation WITH agent-dispatch can
build them (see Anomalies).

prose-review remains FULLY GATED on 03's deferred answer (still deferred, no
## Answers). 04 depends on 01+03; retrofits 05-13 depend on 03. Lease HELD,
now bumped to Generation 6 (pre-seeded specs/prose-review/DRAIN-OWNER.md).

EXHAUSTION PHASE for gen 6 (after dispatching the two pending tasks above):
1. Critique intake, one spec/pass, ≤once per spec per run, skipping the 7
   Intake-failed specs. Remaining eligible (Priority then path):
   retire-static-dashboards, rigor-tier, trajectory-evals,
   workboard-auto-triage (P2), then first-pass-success-rate, harness-audit
   (P3). (large-codebase-context-guide and model-routing-multi-vendor-citations
   are now broken-down, no longer draft-spec candidates.)
2. Stub intake (screen-stub.sh FIRST per stub): agent-tier-leaks/tasks/04,05;
   drain-wake-cost/tasks/04; orchestrator-share-audit/tasks/03;
   spec-completion-review/tasks/04,05. scr/05 (build-mirror gap) likely
   DECISION-SHAPED or refused per gen 2.
3. 3b auto-breakdown: none pending (the two Breakdown-ready specs this gen
   already have tasks/).
4. Batch interview LAST: prose-review 03 deferred question (verbatim below) +
   exit checklist. A headless generation writes it into this baton and stops.

When 03's answer lands and flips it pending: re-dispatch 03, then 04
(mirror+bump closing; bumps plugin.json relative to its own base, currently
0.8.48), then retrofits 05-13 — W=3 authorized for the retrofit group ONLY
(Group: 05..13, pairwise-disjoint Touch; budget then drops to max(2,6-3)=3
units/gen). Retrofits are CROSS-REPO (worktree the TARGET repo per
docs/memory/drain-dispatch-lessons.md); each has a MANDATORY CI paths-ignore
precondition; task 09 (portfolio-tracker) AUTO-PUSHES/AUTO-DEPLOYS on commit —
BLOCK rather than commit if its precondition fails.

## prose-review 03 deferred question (verbatim, for the batch interview)

- 2026-07-11 — Task 03 requires `vale README.md AGENTS.md` to exit 0
  (criterion C2), but its Touch list (`templates/, .claude/skills/gate/,
  vale/styles/config/vocabularies/House/accept.txt`) cannot achieve that: of
  the three error-level alert classes (Google.EmDash 22, Vale.Spelling 22,
  Vale.Terms 2), the Spelling/Terms errors are fixable in accept.txt, but
  Google.EmDash is an existence-type rule (no vocabulary/exceptions mechanism)
  firing on the repo's deliberate spaced-em-dash house style in README.md and
  AGENTS.md. How should C2 be satisfied? (a) Amend the task's Touch to include
  `vale/.vale.ini.template` and centrally disable Google.EmDash there
  (`Google.EmDash = NO` under `[*.md]`) — the minimal fix, endorsing the house
  style; (b) amend Touch to include README.md and AGENTS.md and rewrite all
  spaced em-dashes to Google-style unspaced dashes — conforms to Google style
  but reverses the established house-style repo-wide prose convention; or (c)
  revise the spec/criterion so the bare-vale check excludes Google.EmDash some
  other way. Option (a) matches attempt 1's working implementation.

## Anomalies / carry-forward

- ENVIRONMENT LIMITATION (gen 5, NEW): this drain generation ran in a context
  with NO agent-dispatch tool (no Task/Agent/Team tool in base or deferred
  set — searched exhaustively). Consequences: (a) implementation-workers
  CANNOT be dispatched — the two pending tasks above cannot be BUILT by a
  generation in this same environment; (b) /critique and /breakdown were run
  INLINE (in the hub session's own context via the Skill tool) rather than
  via the critic agent — verdicts are sound but this spends hub context, off
  the wake-economics ideal; (c) a successor generation CANNOT be auto-spawned.
  Per auto-memory (feedback_no_headless_sessions: "human launches every
  generation"), gen 6 is HUMAN-LAUNCHED. A human must relaunch drain for
  gen 6, ideally in an environment where the Task/Agent tool IS available so
  the two pending doc tasks can be built (else gen 6 repeats this limitation
  and can only do more inline critique/breakdown/stub-intake, never build).
- SPEC-COMPLETION REVIEW OBLIGATION (carried): prose-review had tasks 01+02
  complete DONE in an earlier generation, so when it eventually reaches
  nothing-left-to-dispatch and its lease releases, the spec-completion review
  MUST run first (evidence file specs/prose-review/evidence/spec-review.md is
  the idempotency token — still NOT written). Do NOT retro-apply to specs
  drained before the machinery merged (cache-reprime, agentprof-attr,
  drain-forward-progress, spec-completion-review itself). Gen 5 drained NO
  prose-review tasks (fully gated), so no review fired this gen.
- vale side effect: any worker that runs bin/install-vale inside its worktree
  repoints machine-global ~/.vale.ini StylesPath at that worktree; after
  merging/discarding such a branch, re-run `bash bin/install-vale --force`
  from /Users/sjaconette/claude and confirm `grep '^StylesPath' ~/.vale.ini`
  shows /Users/sjaconette/claude/vale/styles. (No such worker ran this gen.)
- Two FOREIGN owner leases live and untouchable: specs/draft-auto-promotion/,
  specs/work-exhaustion/. Never touch specs/agentprof-antigravity-adapter.
- Foreign worktrees/branches in the shared checkout (task/01-verifier-leak-trace,
  task/02-namespace-attribution, task/03-closing-gate, task/03-ship-gate) —
  other sessions' work; never sweep them. Untracked slack-relay/ dir belongs
  to another session.
- plugin.json at 0.8.48; prose-review/04 closing task bumps relative to base.
- Generations cap = 10 (this baton hands to gen 6). Remote/main in sync at
  gen 5 handoff (0 ahead / 0 behind, verified).
