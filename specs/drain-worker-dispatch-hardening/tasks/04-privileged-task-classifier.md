# Task 04: Privileged/OS-level task classifier

Status: done
Depends on: none
Priority: P2
Budget: 15 turns
Spec: ../SPEC.md (requirement R3)
Touch: .claude/skills/breakdown/SKILL.md, antigravity/.agents/skills/breakdown/SKILL.md

## Goal

A task whose acceptance commands require `launchctl`, a system
installer/package-manager install step, or interactive OAuth is flagged
MANUAL / human-pending at breakdown time — never dispatched to a worker
that can only fail BLOCKED on a sandbox denial.

## Touch

The spec's acceptance criterion permits this classifier to land in any of
`.claude/skills/drain/SKILL.md`, `.claude/skills/drain/reference.md`, or
`.claude/skills/breakdown/SKILL.md`. This task places it in
`.claude/skills/breakdown/SKILL.md` specifically (breakdown is where a
task's acceptance commands are first authored, so this is the natural
authoring-time check) — deliberately keeping this task's Touch disjoint
from tasks 01-03/05's `.claude/skills/drain/*` and `drain.md` edits, so
this task can run concurrently with task 01. Do not touch
`.claude/skills/drain/SKILL.md` or `.claude/skills/drain/reference.md`.

`codex/.agents/skills/breakdown` is a symlink to
`antigravity/.agents/skills/breakdown/SKILL.md` (confirmed per
CLAUDE.md's port-chain and SPEC.md's Mirror obligations) — no separate
codex edit is needed once the antigravity file is updated.

## Steps

1. Read `.claude/skills/breakdown/SKILL.md`'s task-authoring procedure
   (the numbered steps where a task's `Touch:`/acceptance criteria get
   written) and `docs/memory/unattended-worker-tool-limits.md`'s existing
   manual-pending precedent ("OR let the worker mark that one criterion
   manual-pending with the reason").
2. Add a classification step: while authoring a task's acceptance
   criteria, if any command requires `launchctl`, a system
   installer/package-manager install step, or interactive OAuth, mark
   that task MANUAL / human-pending instead of drain-completable
   unattended — mirroring the existing manual-pending escape rather than
   inventing new vocabulary. Use the literal phrase "never
   drain-completable unattended" somewhere in this addition (the spec's
   acceptance criterion greps for it).
3. Port the same addition into
   `antigravity/.agents/skills/breakdown/SKILL.md`, adapted per
   `.claude/rules/mirror-procedure-discipline.md` (same steps, same
   order, same stated conditions).
4. Commit.

## Acceptance

- [x] `grep -c "never drain-completable unattended" .claude/skills/breakdown/SKILL.md` → at least 1
- [x] `grep -c "never drain-completable unattended" .claude/skills/drain/SKILL.md .claude/skills/drain/reference.md` → 0 (confirms this task, not a sibling, owns the phrase — the spec's acceptance criterion sums across all three files, so this count only needs to be nonzero somewhere; this check just documents which file carries it)
- [x] `grep -c "never drain-completable unattended" antigravity/.agents/skills/breakdown/SKILL.md` → at least 1

## Evidence

Merged `task/04-privileged-task-classifier` (commits d9e54a0, 241a51f) via
merge commit `01e28fa`. All 3 acceptance greps pass. `./specs/status.sh` and
`claude plugin validate .` green; full `tests/test_*.sh` suite green except
`test_antigravity_parity.sh`/`test_codex_parity.sh`, which fail on a
pre-existing, unrelated `qa-sweep` mirror gap (confirmed present at the
pre-merge base commit `5ad8e20`, tracked by
`qa-sweep-skill-promotion` task 03, later in this queue).
