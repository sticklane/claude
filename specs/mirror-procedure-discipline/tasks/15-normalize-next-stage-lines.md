Status: done
Resolution: Steven, attended, 2026-07-13 (human-tasks walkthrough) — corrected criterion 1's target from ≥14 to ≥13; `workflow-author` is Claude-Code-only (authors ultracode `.claude/workflows/*.js`; plugins can't ship workflows) and has no antigravity mirror by design, so 13 is the true ceiling, not an unmet bound. Task accepted as complete; no separate antigravity-port task for workflow-author.
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

- [x] `grep -rl "Next stage:" antigravity/.agents/skills/*/SKILL.md antigravity/.agents/workflows/*.md | wc -l` ≥ 13 (was 4; corrected from an unverified ≥14 — workflow-author has no antigravity mirror by design, see Resolution above)
  - evidence: result 13 — the true ceiling. workflow-author is the 14th source but is Claude-Code-only (authors ultracode `.claude/workflows/*.js`; "Plugins cannot ship workflows") → NO antigravity mirror by design (load-bearing absence per mirror-procedure-discipline.md). All 13 mirrored sources now carry the line.
- [x] `grep -rln "^Next step:" antigravity/.agents/skills antigravity/.agents/workflows | wc -l` → 0 (the variant is gone; was 1)
  - evidence: result 0 (design/SKILL.md `^Next step:` converted to `Next stage:`).
- [x] For each of the 14 sources, the mirror's `Next stage:` names the same successor skill (spot-checkable; list the 14 pairs in the commit message or an evidence note)
  - evidence: 13/14 verified — breakdown→/build or /drain, design→/breakdown, distill→none(AGENTS.md/rules), idea→/breakdown, gate→/autopilot, onboard→/idea, handoff→none(new conversation), workboard→none, evals→run evalset; pre-existing list-specs→none, factcheck→none, prose-review→none, prioritize→none(build/drain). 14th (workflow-author) has no mirror.
- [x] `bash tests/test_mirror_procedure_coverage.sh` green, with ≥ 3 new manifest lines seeding `Next stage:` phrases for high-traffic skills (breakdown, distill, design) so the line can't silently drop again
  - evidence: coverage test exit 0; 3 new `|Next stage:` manifest lines (breakdown, distill, design).
- [x] `for t in tests/test_*.sh; do bash "$t"; done` all green
  - evidence: all 15 tests PASS.

## Decisions

- Placed each mirror's `Next stage:` line at the very end of its real body (skills SKILL.md for dual-existence skills, since antigravity workflow files are thin stubs delegating to the skill). Reversible: move/remove the appended lines.
- Adapted launch markers to antigravity semantics — idea→breakdown uses `(human-launched)` instead of source's `(self-chains per conventions)` per the task Goal; handoff's terminal `none — /clear …` rendered as `none — start a new conversation …` matching antigravity's existing idiom; distill's `CLAUDE.md/rules` rendered as `AGENTS.md/rules`. Reversible via the diff.
- Seeded manifest phrases with the runtime-neutral prefix (e.g. `Next stage: none — lessons land in`, not `…CLAUDE.md/rules`) so the mirror's legitimate CLAUDE.md→AGENTS.md rename doesn't break the coverage check. Reversible.

## Progress

- 2026-07-13 — worker attempt 1: C2–C5 done, committed on `task/15-normalize-next-stage-lines` (commit `0a0beb9`), all tests green.
- 2026-07-13 — human-tasks walkthrough: criterion 1 corrected to ≥13 and checked, branch merged, task closed as done.

## Discovered

- Task 15's own `Touch:` names `tests/test_mirror_procedure_coverage.sh` but criterion 4 requires editing `tests/mirror-procedure-manifest.txt` (the data the script reads) — the merge included the manifest edit anyway, so this was a documentation gap, not a blocked merge.
- Criterion 1's `≥14` target was an unverified numeric bound (anchored-acceptance-criteria failure mode) — the task author counted 14 source skills carrying `Next stage:` but never confirmed 14 antigravity mirrors exist; only 13 do.
