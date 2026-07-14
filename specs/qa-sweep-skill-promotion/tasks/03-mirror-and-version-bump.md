# Task 03: Antigravity mirror, codex exemption, and plugin version bump

Status: done
Depends on: 01, 02
Priority: P2
Budget: 12 turns
Spec: ../SPEC.md (requirements R1, R7, R8; acceptance criteria 6, 7, 12, 15)
Touch: antigravity/.agents/skills/qa-sweep/SKILL.md, .claude-plugin/plugin.json, codex/README.md

<!-- PLAN (worker, task 03):
1. Reset worktree to main (bcaa562); branch task/03-mirror-and-version-bump.
2. Port .claude/skills/qa-sweep/SKILL.md -> antigravity/.agents/skills/qa-sweep/SKILL.md,
   faithful (R2b-g, R2f contract, R2g two branches); load-bearing adaptations per
   antigravity mechanism: Skill-tool self-chain -> "apply the workflow's procedure",
   Agent tool -> Agent Manager conversations, /critique+/drain -> .agents/workflows/*.md;
   rule + docs/human-gates.md citations kept verbatim (task step 2). Commit.
3. Add anchored "Not ported" qa-sweep row to codex/README.md; NO codex dir. Bump
   plugin.json version 0.9.4->0.9.5 (agents array untouched). Commit.
   NOTE: Edit tool triggers a whole-file markdown formatter on codex/README.md
   (scope creep); injected the single row via python to keep the diff to one line.
4. Gates: full tests/test_*.sh suite + status.sh + plugin validate all green;
   awaited verifier confirmed all 5 criteria + faithful port.
-->

## Goal

`.claude/skills/qa-sweep/SKILL.md` (from task 02) has a working
`antigravity/` mirror at `antigravity/.agents/skills/qa-sweep/SKILL.md`
per this repo's port-chain convention; no `codex/` mirror directory is
created (qa-sweep is not one of the four codex-mirrored skills), but
`codex/README.md`'s "What's not ported" table gains an anchored exemption
row for `qa-sweep` so `tests/test_codex_parity.sh` stays green; and
`.claude-plugin/plugin.json`'s `version` is bumped to reflect the new
skill — with its `agents` array left untouched, since qa-sweep is a
skill, not an agent.

## Touch

Only `antigravity/.agents/skills/qa-sweep/SKILL.md` (new file), the
`version` line of `.claude-plugin/plugin.json`, and the "What's not
ported" table row for `qa-sweep` in `codex/README.md`. Do not touch
`.claude-plugin/plugin.json`'s `agents` array, and do not create any
directory under `codex/.agents/skills/` for qa-sweep.

## Steps

1. Read the finished `.claude/skills/qa-sweep/SKILL.md` (from task 02) in
   full, plus one or two existing paired examples under
   `.claude/skills/*/SKILL.md` and `antigravity/.agents/skills/*/SKILL.md`
   to see how this repo already ports skill procedure into antigravity's
   shape (same steps/order/conditions; only load-bearing runtime
   differences — e.g. a different dispatch tool or headless invocation
   shape — may diverge, per `.claude/rules/mirror-procedure-discipline.md`,
   cited not restated).
2. Note: `antigravity/` has no mirrored counterpart of `.claude/rules/`
   (confirmed by `specs/context-blowout-subagent-guards/SPEC.md`'s R4 —
   no `rules/` directory exists under `antigravity/`). The antigravity
   mirror's citation of `browser-automation-handoffs.md` therefore points
   at the same repo-relative path `.claude/rules/browser-automation-
handoffs.md` as the source skill does — it is not itself mirrored, just
   referenced from the other runtime's skill file. This is not a design
   choice left open; just port the citation as-is.
3. Write `antigravity/.agents/skills/qa-sweep/SKILL.md` as a faithful port
   of the finished `.claude/skills/qa-sweep/SKILL.md`: same procedure,
   same order, same stated conditions (the R2b-g sequence, the R2f
   human-gating contract, the R2g two-branch re-verify), adapted only
   where antigravity's own mechanism forces a difference (e.g. its own
   dispatch/agent-launch primitive if it differs from Claude Code's Agent
   tool — check an existing mirrored pair for the house pattern).
4. Confirm no `codex/.agents/skills/qa-sweep` path was created (codex only
   mirrors drain/build/autopilot/evals).
5. Read `tests/test_codex_parity.sh` and `codex/README.md`'s "What's not
   ported" table (the `fleet`, `workflow-author`, and `critique` rows are
   the house model). Add a new row for `qa-sweep` whose first cell is the
   literal name `qa-sweep` and whose second cell contains the literal
   substring "Not ported", with a one-sentence reason (qa-sweep is not one
   of the four codex-mirrored skills, per root CLAUDE.md's mirror-chain
   convention). Run `bash tests/test_codex_parity.sh` and confirm it exits
   0 with no output.
6. Bump `.claude-plugin/plugin.json`'s `version` field (per root
   CLAUDE.md's "Bump `version` in `plugin.json` whenever skill behavior
   changes") — a patch-level bump is sufficient for a new skill addition.
   Do not touch the `agents` array.

## Acceptance

- [x] `test -f antigravity/.agents/skills/qa-sweep/SKILL.md` → exists — evidence: created, 121 lines
- [x] `test ! -e codex/.agents/skills/qa-sweep` → confirmed absent — evidence: no codex dir created
- [x] `bash tests/test_codex_parity.sh` → exit 0, no output — evidence: green after anchored qa-sweep "Not ported" row added
- [x] `git show <task-base-commit>:.claude-plugin/plugin.json | grep '"version"'` differs from the current file's `"version"` line — confirms the version actually changed from this task's own starting point, not a hard-coded pre-task literal — evidence: base bcaa562 = `0.9.4`, current = `0.9.5`
- [x] `git diff .claude-plugin/plugin.json` touches only the `version` line — no lines inside the `agents` array change — evidence: `git diff bcaa562 -- .claude-plugin/plugin.json` is a single `version` line change
