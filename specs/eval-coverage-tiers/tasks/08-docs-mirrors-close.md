# Task 08: Tier-aware harness-audit, evals docs, mirrors, version bump (closing)

<!-- Machine-read fields; body sections never parsed by orchestrators. -->
<!-- Append-only for workers: flip own Status:, tick checkboxes, add evidence lines, maintain plan block. -->

Status: in-progress
Depends on: 01, 02, 03, 04, 05, 06, 07
Priority: P2
Budget: 10 turns
Spec: ../SPEC.md (requirements R5, R6)
Touch: .claude/skills/harness-audit/SKILL.md, .claude/skills/evals/SKILL.md, .claude/skills/evals/reference.md, codex/.agents/skills/evals/SKILL.md, antigravity/.agents/workflows/evals.md, antigravity/.agents/skills/harness-audit/SKILL.md, .claude-plugin/plugin.json

## Goal

harness-audit's evalset-presence check consults evals/COVERAGE.md
(tier-aware findings: A-gap = finding, B checked against named tests,
C reported waived in one line, missing row = the finding). The evals
skill docs describe the tier table + NN-adv-\* convention in one short
section citing COVERAGE.md. Both codex and antigravity evals mirrors
and the antigravity harness-audit port carry the pointer. plugin.json
bumped. With all R4 tasks landed, the coverage lint is green — the
spec's headline criterion.

## Steps

1. Read tasks 01–07's landed state and the six prose targets.
2. Edit harness-audit + evals SKILL/reference (cite COVERAGE.md, don't
   restate the table), then the three mirror files as paraphrased
   ports.
3. Bump plugin.json; run the mirror-verification sweep on the three
   ports; record evidence.

## Acceptance

- [ ] `bash evals/lint-eval-coverage.sh` → exit 0 (spec headline: the
      policy passes by executing it)
- [ ] `grep -c 'COVERAGE.md' .claude/skills/harness-audit/SKILL.md` ≥ 1
      and `grep -c 'COVERAGE' antigravity/.agents/skills/harness-audit/SKILL.md`
      ≥ 1 (both 0 today, verified 2026-07-19). Depth ceiling: prose
      checklist — behavioral enforcement is the lint criterion above;
      tier-aware wording gets a manual-pending human read.
- [ ] `grep -c 'COVERAGE.md' .claude/skills/evals/SKILL.md` ≥ 1 and
      `grep -c 'COVERAGE.md' codex/.agents/skills/evals/SKILL.md` ≥ 1
      and `grep -c 'COVERAGE' antigravity/.agents/workflows/evals.md`
      ≥ 1 (all 0 today, verified 2026-07-19)
- [ ] `git show <this task's own commit> -- .claude-plugin/plugin.json |
    grep -q '^+.*"version"'` → exit 0
