# Task 05: antigravity mirror + plugin bump + closing gates

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Priority values run P0 (highest) through P3; the header is optional — absent means P2. -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers, in every task file — and ## Progress / ## Deferred questions are drain-written sections (single writer, main checkout): workers report that content, never write it. -->

Status: pending
Depends on: 02, 03, 04
Priority: P1
Budget: 12 turns
Spec: ../SPEC.md (requirement R10)
Touch: antigravity/, .claude-plugin/plugin.json

## Goal

Every skill file changed by tasks 02–04 is byte-mirrored into the
antigravity port (drain SKILL.md + reference.md, build SKILL.md,
autopilot SKILL.md, onboard SKILL.md — at their existing antigravity
paths; the new rules file mirrors per the port's convention for rules,
matching how existing rules are represented there — inspect before
copying), and `.claude-plugin/plugin.json` `version` is bumped once for
the whole spec. Full gate suite green at the end. Note: the spec's
MANUAL-PENDING e2e criterion is human-run and explicitly NOT this
task's (or any worker's) gate.

## Touch

Only `antigravity/` and `.claude-plugin/plugin.json`. Do NOT re-edit the
source skill files — if a mirror diff reveals a source problem, report
it as Discovered, don't fix it here.

## Steps

1. Diff each changed source skill file against its antigravity
   counterpart; copy source → mirror (byte-identical for files the port
   mirrors verbatim; see docs/memory/workboard-mirror-verbatim.md).
2. Determine how the port represents `.claude/rules/` files and mirror
   the new rule accordingly.
3. Bump plugin.json version once.
4. Full gate suite; commit.

## Acceptance

- [ ] For each changed skill file F: `diff .claude/skills/<F> antigravity/.agents/skills/<F>` → no output (byte-mirrored)
- [ ] `git diff main -- .claude-plugin/plugin.json | grep -c '"version"'` → 2 (old + new line)
- [ ] `for t in tests/test_*.sh; do bash "$t" || exit 1; done && ./bin/check-agent-model-pins && ./evals/runner-selftest.sh && ./specs/status.sh && claude plugin validate . && bash evals/lint-ultra-gate.sh` → exit 0
