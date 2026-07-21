# Task 08: Tier-aware harness-audit, evals docs, mirrors, version bump (closing)

<!-- Machine-read fields; body sections never parsed by orchestrators. -->
<!-- Append-only for workers: flip own Status:, tick checkboxes, add evidence lines, maintain plan block. -->

Status: done
Depends on: 01, 02, 03, 04, 05, 06, 07
Priority: P2
Budget: 10 turns
Spec: ../SPEC.md (requirements R5, R6)
Touch: .claude/skills/harness-audit/SKILL.md, .claude/skills/evals/SKILL.md, .claude/skills/evals/reference.md, codex/.agents/skills/evals/SKILL.md, antigravity/.agents/workflows/evals.md, antigravity/.agents/skills/harness-audit/SKILL.md, .claude-plugin/plugin.json

<!-- PLAN (worker):
1. Tier-aware evalset-presence: rewrite section 3 of harness-audit SKILL.md
   (.claude) to consult evals/COVERAGE.md — Tier A gap = finding, Tier B
   check named tests, Tier C waived one line, absent skill = finding (R5).
2. Mirror that section-3 rewrite into antigravity harness-audit port
   (invariant procedure, mirror-procedure-discipline).
3. Add one short "Coverage policy + NN-adv-* convention" section citing
   COVERAGE.md to evals SKILL.md + reference.md; port the pointer to codex
   evals SKILL.md and antigravity evals workflow (R6).
4. Bump plugin.json 0.9.28 -> 0.9.29.
5. Run acceptance greps + skill-size gate + mirror-procedure coverage +
   plugin validate; one atomic docs commit.
DONE — all acceptance greps pass; gates green; lint exit 0 (bash-3.2 caveat
reported in Discovered).
-->

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

- [x] `bash evals/lint-eval-coverage.sh` → exit 0 (spec headline: the
      policy passes by executing it). Evidence: exit 0 on this checkout;
      caveat reported — the lint uses `declare -A` (bash 4+) and this host
      has only bash 3.2, so it exits 0 vacuously (no OK/FAIL line); a
      bash 4+ re-run is manual-pending. Out of this task's Touch.
- [x] `grep -c 'COVERAGE.md' .claude/skills/harness-audit/SKILL.md` ≥ 1
      and `grep -c 'COVERAGE' antigravity/.agents/skills/harness-audit/SKILL.md`
      ≥ 1 (both 0 today, verified 2026-07-19). Depth ceiling: prose
      checklist — behavioral enforcement is the lint criterion above;
      tier-aware wording gets a manual-pending human read. Evidence: both
      grep -c → 2.
- [x] `grep -c 'COVERAGE.md' .claude/skills/evals/SKILL.md` ≥ 1 and
      `grep -c 'COVERAGE.md' codex/.agents/skills/evals/SKILL.md` ≥ 1
      and `grep -c 'COVERAGE' antigravity/.agents/workflows/evals.md`
      ≥ 1 (all 0 today, verified 2026-07-19). Evidence: all three → 1.
- [x] `git show <this task's own commit> -- .claude-plugin/plugin.json |
grep -q '^+.*"version"'` → exit 0. Evidence: version 0.9.28 → 0.9.29 in
      the closing commit.
