Status: blocked
Blocked: criterion 1 (`Next stage:` count ≥14) is unattainable — the true ceiling is 13 because `workflow-author` is Claude-Code-only (ultracode Workflow tool) with no antigravity mirror by design. All other work (C2–C5) is done, committed, and verified on branch task/15-normalize-next-stage-lines.
Unblock: ask: Should criterion 1's target be corrected to ≥13 (workflow-author has no antigravity mirror by design), accepting this task as complete — or should a separate task port workflow-author into the antigravity tree?
Discovered-from: specs/mirror-procedure-discipline/tasks/03-audit-distill.md
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
- [ ] `grep -rln "^Next step:" antigravity/.agents/skills antigravity/.agents/workflows | wc -l` → 0 (the variant is gone; was 1)
- [ ] For each of the 14 sources, the mirror's `Next stage:` names the same successor skill (spot-checkable; list the 14 pairs in the commit message or an evidence note)
- [ ] `bash tests/test_mirror_procedure_coverage.sh` green, with ≥ 3 new manifest lines seeding `Next stage:` phrases for high-traffic skills (breakdown, distill, design) so the line can't silently drop again
- [ ] `for t in tests/test_*.sh; do bash "$t"; done` all green

## Decisions

- Placed each mirror's `Next stage:` line at the very end of its real body (skills SKILL.md for dual-existence skills, since antigravity workflow files are thin stubs delegating to the skill). Reversible: move/remove the appended lines.
- Adapted launch markers to antigravity semantics — idea→breakdown uses `(human-launched)` instead of source's `(self-chains per conventions)` per the task Goal; handoff's terminal `none — /clear …` rendered as `none — start a new conversation …` matching antigravity's existing idiom; distill's `CLAUDE.md/rules` rendered as `AGENTS.md/rules`. Reversible via the diff.
- Seeded manifest phrases with the runtime-neutral prefix (e.g. `Next stage: none — lessons land in`, not `…CLAUDE.md/rules`) so the mirror's legitimate CLAUDE.md→AGENTS.md rename doesn't break the coverage check. Reversible.

## Progress

- 2026-07-13 — worker attempt 1: C2–C5 done, committed on `task/15-normalize-next-stage-lines` (commit `0a0beb9`, unmerged), all tests green. C1 BLOCKED — see `Unblock:` above. Remaining: human decision on C1's numeric target.

## Discovered

- Task 15's own `Touch:` names `tests/test_mirror_procedure_coverage.sh` but criterion 4 requires editing `tests/mirror-procedure-manifest.txt` (the data the script reads) — a merge-time Touch whitelist should include it once this task unblocks. (specs/mirror-procedure-discipline/tasks/15-normalize-next-stage-lines.md)
- Criterion 1's `≥14` target was an unverified numeric bound (anchored-acceptance-criteria failure mode) — the task author counted 14 source skills carrying `Next stage:` but never confirmed 14 antigravity mirrors exist; only 13 do. (specs/mirror-procedure-discipline/tasks/15-normalize-next-stage-lines.md)
