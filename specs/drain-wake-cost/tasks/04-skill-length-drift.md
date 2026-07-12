# Task 04: extract drain SKILL.md heavy prose to reference.md (< 500 lines)

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers. -->

Status: in-progress
Promotion-ready: true
Promoted-by-run: attended-2026-07-12-sjaconette
Discovered-from: specs/drain-wake-cost/tasks/01-drain-skill-text.md
Depends on: none
Priority: P2
Budget: 8 turns
Spec: ../SPEC.md
Touch: .claude/skills/drain/SKILL.md, .claude/skills/drain/reference.md, antigravity/.agents/workflows/drain.md, codex/.agents/skills/drain/SKILL.md, .claude-plugin/plugin.json

## Goal

drain SKILL.md (665 lines today) drops below 500 by RELOCATING heavy
prose to reference.md — content-equivalent moves with section-lookup
pointers left behind (the "load only the named section" pattern the
skill already uses, 3 sites today), never deletion of machinery.
Maintainer decision 2026-07-12 (Steven, interview): extraction
authorized; the alternative (documented exemption) was rejected.
Candidate relocations: long rationale/economics passages whose
procedures stay, verbose sub-procedures already summarized at their call
sites. Execution-critical contracts stay in the first 30 lines per
conventions. The antigravity and codex ports get content-equivalent
pointer adjustments ONLY where their text mirrors a relocated passage
(paraphrased ports — content coverage, not byte-diff). Run the critic on
the diff before close-out (docs/memory/skill-retirement-checklist.md
pattern: a clean grep does not prove semantic completeness).

## Original report

> `.claude/skills/drain/SKILL.md` is now 547 lines, over the "well under
> 500 lines" CLAUDE.md convention — it was already 510 before this task,
> and R3/R4/R6 required additive prose while forbidding machinery
> removal, so it couldn't be reduced here; a future pass could relocate
> some heavy prose to reference.md, but that would alter what the SKILL
> body teaches and is out of this task's scope. Worth tracking as drift
> on the drain skill.

## Acceptance

- [ ] `wc -l < .claude/skills/drain/SKILL.md` → < 500 (665 at authoring)
- [ ] `bash evals/lint-ultra-gate.sh` → OK AND `claude plugin validate .` → passes
- [ ] Every relocated passage reachable via a SKILL.md pointer naming its reference.md heading (MANUAL: spot-check each move; no machinery deleted)
- [ ] Awaited critic on the diff returns READY (no semantic-loss findings)
- [ ] `git show HEAD -- .claude-plugin/plugin.json | grep -q '^+.*"version"'` right after this task's commit → version bumped relative to base
