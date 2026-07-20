# Task 06: Antigravity mirrors and plugin version bump (closing task)

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch, Rigor) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. -->

Status: pending
Depends on: 02, 03, 04
Priority: P2
Budget: 10 turns
Spec: ../SPEC.md (requirement R7)
Touch: antigravity/.agents/skills/idea/SKILL.md, antigravity/.agents/skills/breakdown/SKILL.md, antigravity/.agents/workflows/critique.md, antigravity/.agents/skills/critic/SKILL.md, antigravity/.agents/skills/verifier/SKILL.md, .claude-plugin/plugin.json

## Goal

The five antigravity ports carry the equivalent edits from tasks 02–04
(paraphrased ports, not byte copies — mirror-procedure-discipline's
classification applies; nothing here is a forced divergence, so all five
are faithful carries), and plugin.json's version is bumped. Codex needs
no edits: it symlinks the antigravity skills, and none of its three
real-content wrappers are touched.

## Steps

1. Read tasks 02–04's landed diffs (`git log` on their Touch paths) and
   the five port files.
2. Carry each edit as a port: same procedure, same conditions, adapted
   voice — content-coverage, never byte-diff
   (docs/memory/workboard-mirror-verbatim.md).
3. Bump `.claude-plugin/plugin.json` `version`.
4. Run the closure-triggered mirror cross-reference sweep per
   `.claude/rules/mirror-verification.md` on the five ports; record the
   result as evidence.

## Acceptance

- [ ] `grep -c 'depth ceiling' antigravity/.agents/skills/idea/SKILL.md`
      → ≥ 1; `grep -c 'depth ceiling'
antigravity/.agents/skills/breakdown/SKILL.md` → ≥ 1;
      `grep -ci 'gameable' antigravity/.agents/skills/critic/SKILL.md`
      → ≥ 1; `grep -ci 'gameable'
antigravity/.agents/workflows/critique.md` → ≥ 1;
      `grep -c 'criteria-adequacy'
antigravity/.agents/skills/verifier/SKILL.md` → ≥ 1 (per-file
      anchors — a partial port cannot pass; all five 0 today, verified
      2026-07-19). Depth ceiling: paraphrased-port prose — behavioral
      complement is the mirror-verification live sweep in step 4,
      evidence-recorded.
- [ ] `git show <this task's own commit> -- .claude-plugin/plugin.json |
grep -q '^+.*"version"'` → exit 0 (own-commit version bump, per
      docs/memory/anchored-acceptance-criteria.md)
