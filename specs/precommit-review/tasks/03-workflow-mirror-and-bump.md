# Task 03: antigravity workflow mirror + plugin bump

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Priority values run P0 (highest) through P3; the header is optional — absent means P2. -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers, in every task file — and ## Progress / ## Deferred questions are drain-written sections (single writer, main checkout): workers report that content, never write it. -->

Status: done
Depends on: 02
Priority: P2
Budget: 8 turns
Spec: ../SPEC.md (requirement R7)
Touch: antigravity/.agents/workflows/build.md, .claude-plugin/plugin.json

## Goal

The antigravity port of build — the WORKFLOW at
`antigravity/.agents/workflows/build.md` (build is human-only; per
CLAUDE.md human-only skills mirror as workflows; there is NO
antigravity/.agents/skills/build/) — carries the new review step in the
workflow's own shape (content-mirrored, not byte-identical), and
`.claude-plugin/plugin.json` is bumped one version for the spec.

## Touch

Only the two listed files. Do NOT re-edit build's SKILL.md — if
mirroring reveals a source problem, report it as Discovered.

## Steps

1. Read task 02's merged review step in `.claude/skills/build/SKILL.md`;
   read the workflow's existing structure; port the step faithfully
   (skip gate, reviewer selection, fix policy, single pass, outcome
   line) in the workflow's idiom.
2. Bump plugin.json version once.
3. Acceptance checks + full gates; commit.

## Acceptance

- [x] `for tok in code-review numstat "review skipped"; do grep -qc "$tok" antigravity/.agents/workflows/build.md || exit 1; done` → exit 0 (verified: all three tokens present in the ported close-out step)
- [x] `git diff main -- .claude-plugin/plugin.json | grep -c '"version"'` → 2 (verified: 0.8.6 → 0.8.7)
- [x] `for t in tests/test_*.sh; do bash "$t" || exit 1; done && ./bin/check-agent-model-pins && ./evals/runner-selftest.sh && ./specs/status.sh && claude plugin validate . && bash evals/lint-ultra-gate.sh` → exit 0 (verified: all gates pass, evidence/03-workflow-mirror-and-bump.md)

## Discovered

- [2026-07-05 /drain] antigravity drain.md missing sub-reviewer clause cited by build.md mirror — `antigravity/.agents/workflows/drain.md` has no "sub-reviewer" clause that build.md's mirrored review step cites ("the drain workflow's sub-reviewer clause") — the citation points at prose that doesn't exist in the antigravity drain mirror yet (only in `.claude/skills/drain/reference.md`); worth a follow-up task if drain.md is ever mirrored with that section. Stub: 04-antigravity-drain-sub-reviewer-clause.md
