# Task 01: spec-completion review step in drain

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers. -->

Status: done
Depends on: none
Priority: P1
Budget: 7 turns
Spec: ../SPEC.md (requirements R1, R2, R3, R5)
Touch: .claude/skills/drain/SKILL.md, .claude/skills/drain/reference.md

## Goal

Drain gains the spec-completion review at the lease-release boundary per
SPEC R1/R2/R3/R5: pinned ordering (review → commit evidence line →
release lease) with specs/<slug>/evidence/spec-review.md as the
idempotency token; pinned flip-message contract
`drain: <spec-slug> task NN in-progress` (replacing the current "e.g.")
+ the exact git log recovery command; build's skip gate reused via
--numstat; ONE review-fix worker at implementation-worker pin,
/code-review-equivalent at low effort, high-confidence
correctness/behavior FINDING FILTER, union-Touch bound, task-file
coupling nulled (empty tasks/ whitelist, no DONE bookkeeping); exit
checklist gains the `spec review: N findings, M fixed, K stubbed` line.
Anchors: "spec-completion review" and "spec review skipped" (both 0-hit
today). Ultra-path: run `bash evals/lint-ultra-gate.sh` before commit.
NOTE cross-spec: specs/drain-forward-progress edits the same files —
drain admission serializes via Touch; do not hand-merge its content.

## Acceptance

- [x] `grep -qi 'spec-completion review' .claude/skills/drain/SKILL.md && grep -qi 'spec review skipped' .claude/skills/drain/SKILL.md` → hits — verifier: both hit (evidence/01-drain-step.md)
- [x] `grep -qi 'drain: <spec-slug> task NN in-progress' .claude/skills/drain/SKILL.md` → pinned contract present (MANUAL: "e.g." dropped at that site) — verifier: hit; flip site now pins the contract ("not an example")
- [x] MANUAL: ordering, idempotency token, numstat-only hub, nulled task-file coupling, checklist line all present per R1/R2/R3/R5 — verifier: all present (SKILL.md spec-review section + reference.md worker section)
- [x] `bash evals/lint-ultra-gate.sh` → OK — verifier: prints OK, exit 0
