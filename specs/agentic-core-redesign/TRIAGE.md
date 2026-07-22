# Queue re-triage against the agentic-core-redesign

Migration step 1 (SPEC.md). Every open queue item — each task file with
`Status: pending|blocked|deferred|draft` and each `specs/*/` with no
`tasks/` directory — carries one verdict against this redesign:

- **keep** — still-valid work on a component the redesign preserves.
- **subsumed** — the redesign deletes or replaces the machinery this item
  touches; the task file's `Status:` is flipped to `obsolete` (with a
  `Closed:` line citing this file) so no drain dispatches it. Bare
  subsumed `SPEC.md`s get a row here only — this task's `Touch:` scopes
  header edits to other specs' *task files*, not their `SPEC.md`s; the
  maintainer read of this file before the next drain (Depth ceiling L1)
  keeps them out of auto-breakdown.
- **fold-in** — half-built work whose content should be absorbed into an
  agentic-core-redesign task (fold target named).

## What each verdict rests on

Design anchors (SPEC.md): the redesign **preserves** ctx (S7 — folded into
`agentic ctx`, fronting the existing binary), agentprof, the evals harness
(step 4 evals assert loop behavior), and the workboard (S13 inbox renders
through it). It **deletes or replaces**: the mirror chain and its
manifest/parity gates/sweeps (D5, migration step 5); the drain prose loop,
its markdown-header readers such as `drain_frontier.py`, and the
baton/lease/handoff files (D2, S8, S9, step 4); beads' typed dependency
graph replaces prose coordination registries (D3); composer-injected
context and grants replace "prefer X" adoption prose and manual grant
rollouts (D4); caps + `agentic inbox` replace human-approval / attended-task
gating (D1, step 6); the plugin-bump / port-chain authoring conventions go
with the mirror chain (D5, step 5).

The three subsumed clusters the SPEC pre-named were verified per item, not
assumed: mirror machinery, the drain self-patch cluster, and
ctx-dispatch-adoption's adoption-plumbing. Membership held; ctx-dispatch's
`06` (plugin bump distributing already-shipped skill edits) and `10`
(an agentprof correctness bug) are **keep**, not part of the subsumed
adoption cluster.

**fold-in is empty by finding, not omission.** Every open item resolved to
either work on a surviving component (keep) or work on deleted/replaced
machinery (subsumed). No item is partially-built redesign work that an
agentic task must absorb — the redesign's own task graph (SPEC.md coverage
table) already carries every construction and deletion obligation.

## Verdicts — open task files

specs/ctx-absence-check/tasks/03-docs-absence-fallacy-update.md · keep · ctx behavior docs; ctx survives as agentic ctx (S7)
specs/ctx-absence-check/tasks/04-suggested-check-grep-not-literal.md · keep · ctx suggested-grep correctness bug; ctx survives (S7)
specs/ctx-absence-check/tasks/05-json-no-match-omits-did-you-mean-candidates.md · keep · ctx JSON/text output parity; ctx survives (S7)
specs/ctx-cujs/tasks/02-skill-link-and-typo-fix.md · keep · ctx skill doc link + map-flag typo; ctx survives (S7)
specs/ctx-doc-drift-gate/tasks/02-stale-claims-sweep.md · keep · ctx doc conformance sweep; ctx survives (S7)
specs/ctx-doc-drift-gate/tasks/03-waiver-retirement.md · keep · ctx doc-conformance waiver retirement; ctx survives (S7)
specs/ctx-doc-drift-gate/tasks/04-reverse-coverage-builtin-noise.md · keep · ctx doc_conformance report tooling; ctx survives (S7)
specs/ctx-doc-drift-gate/tasks/05-ctx-cujs-show-command-doc-drift.md · keep · ctx guide accuracy fix; ctx survives (S7)
specs/ctx-output-shape-gaps/tasks/02-tree-files-mode.md · keep · ctx tree --files feature; ctx survives (S7)
specs/ctx-output-shape-gaps/tasks/03-skill-docs-rows.md · keep · ctx skill docs for --files mode; ctx survives (S7)
specs/ctxignore-git-overlay/tasks/03-bare-pattern-basename-vs-directory-mismatch.md · keep · ctx .ctxignore overlay behavior bug; ctx survives (S7)
specs/codebase-context-tree/tasks/15-file-size-cast-overflow.md · keep · ctx index staleness cast overflow; ctx survives (S7)
specs/codebase-context-tree/tasks/16-map-ranking-bash-locals.md · keep · ctx map ranking quality; ctx survives (S7)
specs/agentprof-skill-audit/tasks/05-judge-fake-replies-mode.md · keep · agentprof judge test infra; agentprof survives
specs/agentprof-skill-audit/tasks/06-skillcheck-readme-doc.md · keep · agentprof README subcommand doc; agentprof survives
specs/agentprof-skill-audit/tasks/07-skill-invocation-source-line.md · keep · agentprof SkillInvocation feature; agentprof survives
specs/agentprof-skill-audit/tasks/08-possible-miss-false-positive-check.md · keep · agentprof DetectPossibleMisses correctness; agentprof survives
specs/ctx-dispatch-adoption/tasks/06-plugin-bump-close.md · keep · closing plugin.json bump distributes shipped skill edits; valid until cutover (its mirror-sweep half is moot but the bump is not)
specs/ctx-dispatch-adoption/tasks/10-agentprof-skill-invocations-wrong-field.md · keep · agentprof reads input.command not input.skill — correctness bug in a surviving tool
specs/eval-coverage-tiers/tasks/09-lint-vacuous-pass-missing-skills-dir.md · keep · evals lint vacuous-pass bug; evals survive/expand (step 4)
specs/eval-coverage-tiers/tasks/10-run-sh-shared-dep-provisioning.md · keep · evals runner shared-dep provisioning; evals survive (step 4)
specs/eval-coverage-tiers/tasks/11-idea-adv-doctrine-grep-unanchored-marker-scope.md · keep · eval grader scoping bug; evals survive (step 4)
specs/trajectory-evals/tasks/07-scout-trajectory-grep-field-confirmation.md · keep · eval grader stream-json field confirmation; evals survive (step 4)
specs/workboard-kanban-view/tasks/02-kanban-column-closed-status-guard.md · keep · workboard robustness; workboard survives, inbox renders through it (S13)
specs/workboard-kanban-view/tasks/03-agents-md-board-route-doc.md · keep · documents a shipped workboard route; workboard survives (S13)
specs/drain-multi-spec-swarm/tasks/08-skillmd-overstates-admission-cli.md · subsumed · patches drain SKILL.md prose loop, replaced by the agentic CLI loop (D2/S8)
specs/drain-multi-spec-swarm/tasks/09-codex-skillmd-mangled-markdown.md · subsumed · fixes codex mirror of drain SKILL.md; mirror chain deleted (D5, step 5)
specs/drain-multi-spec-swarm/tasks/10-git-cas-claim-idempotent-reclaim-raises.md · subsumed · hardens the DRAIN-OWNER git-CAS lease; lease files deleted (S9, step 4)
specs/drain-frontier-scanner/tasks/05-worker-verifier-orphan-guard.md · subsumed · hardens the prose worker/verifier procedure; replaced by the coded loop + verdict-file transport (S5/S8)
specs/drain-frontier-scanner/tasks/06-status-vocabulary-missing-draft-obsolete.md · subsumed · bug in drain_frontier.py, a markdown-header reader retired at cutover (step 4)
specs/drain-frontier-scanner/tasks/07-cross-spec-landing-order-not-machine-readable.md · subsumed · prose landing-order registry replaced by beads typed dependencies (D3)
specs/ctx-dispatch-adoption/tasks/05-repo-allowlist-rollout.md · subsumed · manual Bash(ctx *) grant rollout replaced by composer-injected grants (D4)
specs/ctx-dispatch-adoption/tasks/07-antigravity-breakdown-skill-scout-only-parity-gap.md · subsumed · antigravity mirror parity; mirror chain deleted (D5, step 5)
specs/ctx-dispatch-adoption/tasks/08-critic-index-first-manifest-seed-gap.md · subsumed · seeds the mirror-procedure manifest; manifest and its coverage gate deleted (step 5)
specs/ctx-dispatch-adoption/tasks/09-antigravity-onboard-wrapper-guardrail-consolidation.md · subsumed · antigravity mirror content placement; mirror chain deleted (D5, step 5)
specs/trajectory-evals/tasks/05-codex-evals-teardown-mirror-gap.md · subsumed · codex mirror parity gap; mirror chain deleted (D5, step 5)
specs/trajectory-evals/tasks/06-closing-task-version-diff-criterion-fragility.md · subsumed · hardens the plugin.json closing-bump criterion; plugin-bump/port-chain convention deleted (D5, step 5)
specs/narrow-autopilot/tasks/07-antigravity-build-md-char-cap.md · subsumed · antigravity workflow char-cap conformance; mirror chain deleted (D5, step 5)

## Verdicts — specs with no tasks/ directory

specs/agentprof-otel-ingestion/SPEC.md · keep · agentprof OTel-ingestion feature; agentprof survives
specs/ctx-dead-code-zones/SPEC.md · keep · ctx dead-code-zone indexing feature; ctx survives (S7)
specs/ctx-minified-skip/SPEC.md · keep · ctx indexer minified-skip feature; ctx survives (S7)
specs/ctx-query-ergonomics/SPEC.md · keep · ctx query-CLI ergonomics feature; ctx survives (S7)
specs/ctx-skill-token-doctrine/SPEC.md · keep · ctx skill reading/triggering doctrine; ctx survives (S7) — its SKILL.md landing-order registry sub-part is what bd deps (D3) later replace, but the spec's deliverable stands
specs/ctx-static-analysis-augmentation/SPEC.md · keep · ctx static-analysis augmentation (design-gated); ctx survives (S7)
specs/shell-text-tool-doctrine/SPEC.md · keep · agent shell-tool context-habit guidance; prose kept for judgment/context habits (D2, classified at step 8)
specs/skills-vs-ultracode-eval/SPEC.md · keep · standalone toolkit-vs-ultracode measurement; independent of the redesign's deletions
specs/attended-task-human-boundedness/SPEC.md · subsumed · tightens attended-task/human-approval filing; approvals replaced by caps + agentic inbox (D1, step 6)
specs/critique-breakdown-self-chain-gap/SPEC.md · subsumed · fixes a prose launch-gate self-chain gap; launch-contract gating deleted, chaining becomes the coded loop (D2/S8, step 6)
specs/deterministic-skill-chaining/SPEC.md · subsumed · code-mediated skill chaining is delivered by the agentic loop itself (D2/S8; SPEC coverage maps S8 to task 08)
specs/drain-read-once-discipline/SPEC.md · subsumed · hardens how agents read drain's prose reference.md; the prose loop is replaced by code (D2/S8)
