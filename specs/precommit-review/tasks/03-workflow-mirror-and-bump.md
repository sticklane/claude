# Task 03: antigravity workflow mirror + plugin bump

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Priority values run P0 (highest) through P3; the header is optional — absent means P2. -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers, in every task file — and ## Progress / ## Deferred questions are drain-written sections (single writer, main checkout): workers report that content, never write it. -->

Status: in-progress
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

- [ ] `for tok in code-review numstat "review skipped"; do grep -qc "$tok" antigravity/.agents/workflows/build.md || exit 1; done` → exit 0
- [ ] `git diff main -- .claude-plugin/plugin.json | grep -c '"version"'` → 2 (old + new line)
- [ ] `for t in tests/test_*.sh; do bash "$t" || exit 1; done && ./bin/check-agent-model-pins && ./evals/runner-selftest.sh && ./specs/status.sh && claude plugin validate . && bash evals/lint-ultra-gate.sh` → exit 0
