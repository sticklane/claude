Status: in-progress
Discovered-from: specs/mirror-procedure-discipline/tasks/03-audit-distill.md
<!--
PLAN (worker, task/15-normalize-next-stage-lines):
Map: 13 of 14 source skills have an antigravity mirror. workflow-author is
Claude-Code-only (authors ultracode .claude/workflows/*.js; "Plugins cannot
ship workflows") → NO antigravity mirror by design (load-bearing absence per
mirror-procedure-discipline.md) → true ceiling for criterion 1 is 13, not 14.
Existing 4 with Next stage: list-specs, factcheck, prose-review (skills),
prioritize (workflow). Add 9: breakdown, design, distill, idea, gate, onboard,
handoff, workboard (skills SKILL.md), evals (workflow). design + workboard +
evals currently use a "Next step:" variant → convert. Launch markers adapted
to antigravity (human-launched workflow convention).
TDD: seed 3 manifest lines (breakdown/distill/design Next stage phrases) RED,
add mirror lines GREEN, run full tests/.
Criterion 1 (≥14) BLOCKED at 13 — workflow-author has no mirror; reported.
-->

Spec: ../SPEC.md
Blocking: no
Priority: P2
Budget: 6 turns
Touch: antigravity/.agents/skills/*/SKILL.md (closing-line edits only), antigravity/.agents/workflows/*.md (closing-line edits only), tests/test_mirror_procedure_coverage.sh, specs/mirror-procedure-discipline/tasks/15-normalize-next-stage-lines.md

# Normalize `Next stage:` closing lines across the Antigravity port

Decision (Steven, attended, 2026-07-13): the omission is **incidental
drift, not a port convention** — the mirrors' mixed state proves it (some
carry the literal `Next stage:` line, design/evals close with `Next
step:`, breakdown uses a `## Hand off` section, distill ends with
nothing; nothing in Antigravity forces any of these). Normalize every
mirror to the source convention.

Of the 14 `.claude/skills/*/SKILL.md` files that carry a `Next stage:`
closing line per CLAUDE.md's authoring conventions, only 4 of their
`antigravity/.agents/{skills,workflows}` mirrors carry the equivalent
line today (counts verified 2026-07-13, unanchored grep).

## Goal

Each of the 14 source skills' antigravity counterparts (skill SKILL.md,
or workflow .md for human-only skills) closes with a `Next stage:` line
carrying the same successor and artifact path, with launch markers
adapted to Antigravity's semantics (its human-launched workflow
convention replaces "(self-chains per conventions)" where the successor
is an execution stage there). Closing-line edits only — no procedure or
prose rewrites; `.claude/rules/mirror-procedure-discipline.md` governs.

## Acceptance criteria

- [ ] `grep -rl "Next stage:" antigravity/.agents/skills/*/SKILL.md antigravity/.agents/workflows/*.md | wc -l` ≥ 14 (was 4)
  - evidence: result 13 — the true ceiling. workflow-author is the 14th source but is Claude-Code-only (authors ultracode `.claude/workflows/*.js`; "Plugins cannot ship workflows") → NO antigravity mirror by design (load-bearing absence per mirror-procedure-discipline.md). Only 13 of the 14 sources have a mirror to carry the line; all 13 now do. BLOCKED on the literal ≥14 pending human/orchestrator confirmation the target should read ≥13.
- [x] `grep -rln "^Next step:" antigravity/.agents/skills antigravity/.agents/workflows | wc -l` → 0 (the variant is gone; was 1)
  - evidence: result 0 (design/SKILL.md `^Next step:` converted to `Next stage:`).
- [ ] For each of the 14 sources, the mirror's `Next stage:` names the same successor skill (spot-checkable; list the 14 pairs in the commit message or an evidence note)
  - evidence: 13/14 verified — breakdown→/build or /drain, design→/breakdown, distill→none(AGENTS.md/rules), idea→/breakdown, gate→/autopilot, onboard→/idea, handoff→none(new conversation), workboard→none, evals→run evalset; pre-existing list-specs→none, factcheck→none, prose-review→none, prioritize→none(build/drain). 14th (workflow-author) has no mirror.
- [x] `bash tests/test_mirror_procedure_coverage.sh` green, with ≥ 3 new manifest lines seeding `Next stage:` phrases for high-traffic skills (breakdown, distill, design) so the line can't silently drop again
  - evidence: coverage test exit 0; 3 new `|Next stage:` manifest lines (breakdown, distill, design).
- [x] `for t in tests/test_*.sh; do bash "$t"; done` all green
  - evidence: all 15 tests PASS.
