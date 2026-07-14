# Task 03: Sweep remaining /autopilot mentions across docs/, CLAUDE.md, README.md, and friends

Status: pending
Depends on: 01
Priority: P1
Budget: 13 turns
Spec: ../SPEC.md (requirement R6, core-tree portion — excludes codex/ and antigravity/, which are Tasks 04 and 05)
Touch: docs/external-playbooks.md, docs/decisions/orchestrator-context.md, docs/decisions/orchestration.md, docs/memory/unattended-worker-tool-limits.md, docs/memory/worktree-base-tracking-ref.md, docs/memory/skill-retirement-checklist.md, docs/memory/multi-runtime-live-testing.md, docs/TASKS.md, .claude/skills/fleet/SKILL.md, .claude/skills/gate/reference.md, .claude/skills/resume-handoff/SKILL.md, CLAUDE.md, README.md, AGENTS.md, agent-console/agent-console.py, bin/check-token-discipline, tests/mirror-procedure-manifest.txt, runtimes/codex.md, runtimes/README.md, runtimes/claude-code.md, evals/autopilot/

## Goal

Every living `/autopilot` reference in the core (non-codex, non-antigravity)
tree is updated to describe `/build`'s bounded mode, reworded to the
three-skill set (`drain`/`build`/`evals`), or deleted where the referent no
longer exists — EXCEPT the four files R6 exempts (historical research
records or past-incident citations, listed in Acceptance below), which keep
their `/autopilot` mentions unchanged.

## Touch

Exactly the files listed above (re-verify each file's current line numbers
before editing — the spec's own line-number citations are snapshots, not a
contract; find hits by section content via `grep -n autopilot <file>`).
Do not touch `codex/` (Task 04), `antigravity/` (Task 05), or any file
Task 01/02 already own.

## Steps

1. `docs/external-playbooks.md`, `docs/decisions/orchestrator-context.md`,
   `docs/decisions/orchestration.md`, `docs/memory/unattended-worker-tool-limits.md`,
   `docs/memory/worktree-base-tracking-ref.md`, `docs/memory/skill-retirement-checklist.md`,
   `.claude/skills/fleet/SKILL.md` (frontmatter trigger phrase and a body
   mention), `.claude/skills/gate/reference.md`: each is updated to
   describe `/build`'s bounded mode where it previously described
   `/autopilot`.
2. `CLAUDE.md` has three separate mentions: the execution-stages doctrine
   line drops `/autopilot` only, becoming "`/build`, `/drain`,
   `/prioritize`" (NOT `/evals` — that stage stays carved out elsewhere in
   the same doctrine block as never model-invocable; do not add it here).
   The codex-leg authoring convention naming "the four explicit-invocation-only
   skill wrappers — drain/build/autopilot/evals" and "the four
   `.claude/skills/{drain,build,autopilot,evals}/SKILL.md` files" both
   become the three-skill set (drain/build/evals).
3. `.claude/skills/resume-handoff/SKILL.md`'s "four gated execution stages
   (`/build`, `/autopilot`, `/drain`, `/prioritize`)" drops `/autopilot`,
   becoming the three-stage list.
4. `docs/TASKS.md`'s item naming "`build`, `drain`, and `autopilot`
   SKILL.md files" drops "and `autopilot`".
5. `docs/memory/multi-runtime-live-testing.md`'s "drain`/`build`/`autopilot`/`evals`"
enumeration drops `autopilot`, becoming the three-skill set.
6. `README.md` has four spots: the pipeline-stage ASCII diagram drops the
   `/autopilot` column; the command-reference table loses its `/autopilot`
   row; the launch-authorization sentence drops `/autopilot` from its
   parenthetical stage list; the codex-wrapper paragraph becomes the
   three-skill set.
7. `AGENTS.md`'s `codex/` bullet ("four real-content wrappers
   (drain/build/autopilot/evals)") becomes the three-skill set.
8. `agent-console/agent-console.py`'s comment citing "the drain/autopilot
   reference docs" rewords to "drain/build".
9. `bin/check-token-discipline`'s `IN_SCOPE` list drops its two
   `.claude/skills/autopilot/{SKILL,reference}.md` lines outright.
10. `tests/mirror-procedure-manifest.txt`: delete the source→mirror pairing
    line `.claude/skills/autopilot/SKILL.md|antigravity/.agents/workflows/autopilot.md|bounded goal`
    outright — its source is deleted by Task 01, so the coverage test
    skips it regardless of landing order. Do NOT add a replacement pairing
    line here: that line's mirror side (`antigravity/.agents/workflows/build.md`)
    only gets the phrase from Task 04, which runs concurrently with this
    task with no ordering guarantee between them — adding it here would
    make this task's own worktree fail the repo's mirror-coverage test
    (source has the phrase from Task 01, mirror doesn't yet, in this
    task's isolated view). Task 06 adds the replacement line once both
    legs have landed. Do not touch the file's other exempted `autopilot`
    mentions (its header-comment citing "codex-autopilot's content-swap"
    and a long-form note about an unrelated skill's port).
11. `runtimes/codex.md`'s "the four launch-gated skills
    (`drain`/`build`/`autopilot`/`evals`, `allow_implicit_invocation: false`)"
    becomes the three-skill set. `runtimes/README.md`'s two mentions ("the
    drain and autopilot references," "the drain/autopilot headless
    fallbacks") and `runtimes/claude-code.md`'s "the drain and autopilot
    headless fallbacks" all reword `autopilot` → `build`.
12. Delete `evals/autopilot/01-security-refusal/` outright (the whole
    evalset directory — `prompt.txt`, `setup.sh`, `assert.sh` — grading a
    skill that no longer exists).
13. Leave these four files' `/autopilot` mentions UNCHANGED (confirmed
    exempt — historical research or past-incident citations, not
    descriptions of autopilot's current role):
    `docs/orchestration-research-2026-07.md`,
    `.claude/rules/mirror-procedure-discipline.md` (the
    "codex-autopilot content-swap fix" citation),
    `tests/mirror-procedure-manifest.txt` (its OTHER mentions, per step 10),
    `tests/test_check_token_discipline.sh` (the "relaunch clean" design
    example).

## Acceptance

- [ ] `[ ! -d evals/autopilot ]`
- [ ] `! grep -q '\.claude/skills/autopilot/SKILL\.md\|\.claude/skills/autopilot/reference\.md' bin/check-token-discipline`
- [ ] `! grep -q '^\.claude/skills/autopilot/SKILL\.md|' tests/mirror-procedure-manifest.txt`
- [ ] `grep -c autopilot CLAUDE.md` returns 0, and CLAUDE.md's codex-leg
      authoring convention names the three-skill set (`drain`/`build`/`evals`).
- [ ] `grep -qc '\`/build\`, \`/drain\`, \`/prioritize\`' CLAUDE.md && ! grep -qc '\`/build\`, \`/drain\`, \`/evals\`' CLAUDE.md`
- [ ] `! grep -q autopilot docs/external-playbooks.md docs/decisions/orchestrator-context.md docs/decisions/orchestration.md docs/memory/unattended-worker-tool-limits.md docs/memory/worktree-base-tracking-ref.md docs/memory/skill-retirement-checklist.md docs/memory/multi-runtime-live-testing.md docs/TASKS.md .claude/skills/fleet/SKILL.md .claude/skills/gate/reference.md .claude/skills/resume-handoff/SKILL.md README.md AGENTS.md agent-console/agent-console.py runtimes/codex.md runtimes/README.md runtimes/claude-code.md`
- [ ] `grep -c autopilot docs/orchestration-research-2026-07.md .claude/rules/mirror-procedure-discipline.md tests/test_check_token_discipline.sh` — each returns >0 (confirmed still present, per the exemption list; not a regression).
