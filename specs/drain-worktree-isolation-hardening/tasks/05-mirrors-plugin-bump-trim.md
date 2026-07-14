# Task 05: Mirror obligations, plugin version bump, and SKILL.md line-budget trim (R5)

Status: in-progress
Depends on: 01, 02, 03, 04
Priority: P2
Budget: 25 turns
Spec: ../SPEC.md (requirements R5, plus the spec-wide line-budget and gate
acceptance criteria)
Touch: antigravity/.agents/workflows/drain.md, codex/.agents/skills/drain/SKILL.md, .claude-plugin/plugin.json, .claude/skills/drain/SKILL.md, .claude/skills/drain/reference.md

## Goal

Every change tasks 01–04 made to `.claude/skills/drain/SKILL.md` and
`.claude/skills/drain/reference.md` is mirrored into
`antigravity/.agents/workflows/drain.md` (the antigravity mirror of drain's
combined SKILL.md+reference.md content) and `codex/.agents/skills/drain/SKILL.md`
(a real file, not a symlink — one of the four explicit-invocation skills
codex mirrors as real content), each in that mirror's own paraphrased voice
per `docs/memory/workboard-mirror-verbatim.md` — not byte-identical, but
covering the same concepts (default-ON orchestrator isolation + opt-out +
fallback; owner-lease re-read before every status-flip commit; the
mechanical preflight sweep with its live-session liveness definition and
fail-safe skip; and the worktree-before-branch-deletion ordering in both
named locations). `.claude-plugin/plugin.json`'s version is bumped once,
a minor bump over 0.8.63 (this spec adds new capability — R1's default
isolation, R3's preflight sweep — so minor, not patch, per CLAUDE.md's
semver convention). `.claude/skills/drain/SKILL.md` ends this spec
genuinely below the repo's 500-line convention with headroom (it started
at 517, already over, before this spec's four requirement-additions).

## Touch

`antigravity/.agents/workflows/drain.md` (1056 lines currently — the
antigravity mirror target; `antigravity/.agents/skills/drain/` itself holds
only `README.md` and `screen-stub.sh`, not the procedural mirror, so don't
edit those two files for this spec). `codex/.agents/skills/drain/SKILL.md`
(484 lines currently, real file). `.claude-plugin/plugin.json` (version
bump only). `.claude/skills/drain/SKILL.md` and
`.claude/skills/drain/reference.md` (line-budget trim only — no new
requirement content; tasks 01–04 already landed all R1–R4 content).

## Steps

1. Read `../SPEC.md` in full, including all five requirements and the
   Acceptance criteria section, so you know exactly what tasks 01–04
   changed.
2. Read the current diff of `.claude/skills/drain/SKILL.md` and
   `.claude/skills/drain/reference.md` since this spec's base commit
   (`git log --oneline -- .claude/skills/drain/` or `git diff <base>..HEAD --
.claude/skills/drain/`) to get the exact new content to mirror.
3. Read `antigravity/.agents/workflows/drain.md` and
   `codex/.agents/skills/drain/SKILL.md` to find each mirror's existing
   structure and voice (per `docs/memory/workboard-mirror-verbatim.md`,
   these are paraphrased ports — match the mirror's own style, don't paste
   verbatim `.claude/` prose). Apply `.claude/rules/mirror-procedure-discipline.md`'s
   classification: each procedural difference you're about to introduce
   should carry the SAME steps, order, and stated conditions as the
   `.claude/` source unless a runtime mechanism forces a difference (state
   which, if any, apply here — antigravity/codex's dispatch/launch
   primitives may differ, but the sweep/re-read/ordering LOGIC should not).
4. Update both mirrors to cover: R1 (default orchestrator isolation +
   opt-out + fallback), R2 (re-read before every status-flip commit), R3
   (mechanical preflight sweep + live-session liveness + fail-safe skip),
   and R4 (worktree-before-branch-deletion ordering in both named
   locations).
5. Bump `.claude-plugin/plugin.json`'s `"version"` field: a minor bump over
   the base-commit value of 0.8.63 (e.g. 0.9.0) — confirm the base value
   with `git show <base-commit>:.claude-plugin/plugin.json | grep version`
   rather than assuming 0.8.63 is still current at your base (a sibling
   task or spec may have bumped it first; if so, minor-bump from whatever
   value is actually at your base).
6. Run `bash tests/test_mirror_procedure_coverage.sh` if it exists in this
   repo, and fix any reported gap.
7. Check `wc -l < .claude/skills/drain/SKILL.md`. If it is not genuinely
   below 500 with headroom, trim redundant/verbose prose from SKILL.md —
   preferring to move detail into `.claude/skills/drain/reference.md`
   (which has no line-budget convention) over deleting substance — until it
   is. Do not remove any of the R1–R4 anchor phrases or content tasks 01–04
   added; trim only surrounding prose.
8. Run `bash evals/lint-ultra-gate.sh` and fix any drift.
9. Run the full gate suite: `for t in tests/test_*.sh; do bash "$t"; done`,
   `./bin/check-agent-model-pins`, `./evals/runner-selftest.sh`,
   `./specs/status.sh`, `claude plugin validate .` — fix any failure before
   calling this task done.
10. Write a MANUAL-PENDING note in this task's Progress section (per
    `.claude/rules/mirror-verification.md`'s "Manual-pending escape for
    unattended workers") pointing at the spec's MANUAL-PENDING acceptance
    item below — you cannot execute it yourself (`/drain` requires
    live-user launch authorization, which an unattended worker lacks per
    CLAUDE.md's "Authoring conventions" and
    `docs/memory/unattended-worker-tool-limits.md`).

## Acceptance

- [ ] `diff` (or this repo's mirror-conformance check) shows `antigravity/.agents/workflows/drain.md` and `codex/.agents/skills/drain/SKILL.md` updated in step with every changed `.claude/skills/drain/` file — confirm by grepping each mirror for the R1–R4 concepts (e.g. orchestrator isolation, re-read before every status-flip, preflight sweep, worktree-before-branch-deletion) rather than a byte diff, since these are paraphrased ports
- [ ] `git diff <base>..HEAD -- .claude-plugin/plugin.json | grep -c '"version"'` → 2 (one removed, one added line), and the added line's value is a minor bump over the base commit's value (`git show <base-commit>:.claude-plugin/plugin.json | grep version`)
- [ ] `wc -l < .claude/skills/drain/SKILL.md` → genuinely below 500 with headroom
- [ ] `bash evals/lint-ultra-gate.sh` → exit 0
- [ ] `for t in tests/test_*.sh; do bash "$t"; done` → all exit 0
- [ ] `./bin/check-agent-model-pins` → exit 0
- [ ] `./evals/runner-selftest.sh` → exit 0
- [ ] `./specs/status.sh` → exit 0
- [ ] `claude plugin validate .` → exit 0
- [ ] MANUAL-PENDING (human-run; `/drain` requires live-user launch
      authorization, per CLAUDE.md's "Authoring conventions" and
      `docs/memory/unattended-worker-tool-limits.md`): in an attended
      terminal, invoke `/drain` with no argument on a shared (non-worktree)
      checkout and confirm the orchestrator itself now operates from an
      isolated VCS checkout/worktree by default (R1), then confirm a repo
      carrying the documented opt-out header instead runs from the shared
      checkout as before; separately, stage two decoy `DRAIN-OWNER.md`
      leases (one FRESH, one backdated stale) plus one orphaned worktree
      with no corresponding task, invoke `/drain` again, and observe the
      preflight sweep (R3) reclaim the stale lease and prune the orphaned
      worktree while leaving the fresh one alone; separately, force a
      branch-still-checked-out-in-a-worktree deletion attempt on a survivor
      branch and confirm the ordering fix (R4) removes the worktree first
      without erroring; record transcripts in
      `specs/drain-worktree-isolation-hardening/evidence/`
