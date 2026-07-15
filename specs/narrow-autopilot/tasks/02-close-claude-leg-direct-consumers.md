# Task 02: Update onboard/drain/gate/breakdown/human-gates pointers off autopilot

Status: in-progress
Depends on: 01
Priority: P1
Budget: 5 turns
Spec: ../SPEC.md (requirements R3, R4, R5)
Touch: .claude/skills/onboard/SKILL.md, .claude/skills/drain/reference.md, .claude/skills/gate/SKILL.md, .claude/skills/breakdown/SKILL.md, docs/human-gates.md

## Goal

Every `.claude`-leg skill that directly cited or routed to `/autopilot`
now points at `/build`'s bounded mode or `/drain` instead, and
`docs/human-gates.md`'s two remaining `/autopilot` mentions are corrected.

## Touch

Exactly the five files listed above. Do not touch `.claude/skills/build/`
(Task 01 owns it), the antigravity or codex mirrors of gate/breakdown
(later tasks own those trees), or any other doc.

## Steps

1. `onboard/SKILL.md:78-79`'s pointer to the scoped-permissions JSON
   template: change from `autopilot/reference.md` to `build/reference.md`.
2. `drain/reference.md` has two separate `/autopilot` mentions (find by
   section content, not by re-reading the line numbers in the spec — they
   are snapshots, not a contract): the citation of "the autopilot
   reference's headless rule" now cites `build/reference.md`; the
   "Orchestrator isolation (default ON)" paragraph's "Build/autopilot
   worktrees..." drops the `/autopilot` mention.
3. `gate/SKILL.md` has two separate `/autopilot` mentions: its closing
   `Next stage: /autopilot specs/<slug>/tasks/NN-*.md (human-launched)`
   becomes `Next stage: /build specs/<slug>/tasks/NN-*.md (human-launched;
/goal-bound it per build/reference.md for an unattended-feeling run)`;
   the prose sentence just above it ("...with gates in place, tasks
   qualify for `/autopilot`. Close with:") becomes "...with gates in
   place, tasks qualify for an unattended `/goal`-bounded `/build` run (or
   `/drain` for a queue). Close with:".
4. `breakdown/SKILL.md:166`'s routing sentence recommending `/autopilot`
   "for unattended execution of peripheral tasks" is reworded to recommend
   `/drain` for queue/unattended work and `/build` (optionally
   `/goal`-bounded) for a single task.
5. `docs/human-gates.md`: confirm its two remaining `/autopilot` mentions
   with `grep -n autopilot docs/human-gates.md` first (numbers may have
   shifted). The opening list of launch-authorization-contract stages
   ("`/build`, `/autopilot`, `/drain`, `/prioritize` — are model-invocable
   since 2026-07-11") drops `/autopilot`, becoming "`/build`, `/drain`,
   `/prioritize`". Reason 2's "`/autopilot` and `/drain` open with ... a
   classification gate" becomes "`/build`'s bounded mode and `/drain` open
   with ... a classification gate".

## Acceptance

- [ ] `onboard/SKILL.md` and `drain/reference.md` point at
      `build/reference.md`, not `autopilot/reference.md`:
      `! grep -q 'autopilot/reference' .claude/skills/onboard/SKILL.md .claude/skills/drain/reference.md`
- [ ] `gate/SKILL.md` and `breakdown/SKILL.md` close with the replacement
      `Next stage:`/routing text — neither is left pointing at a deleted
      skill: `! grep -q '/autopilot' .claude/skills/gate/SKILL.md .claude/skills/breakdown/SKILL.md`
- [ ] `grep -c autopilot docs/human-gates.md` returns 0.
- [ ] `docs/human-gates.md`'s opening launch-authorization-contract stage
      list reads `/build`, `/drain`, `/prioritize`, and Reason 2 reads
      "`/build`'s bounded mode and `/drain`" — spot check both by reading
      the surrounding lines after the grep above.
