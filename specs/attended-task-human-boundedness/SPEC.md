# Attended-only tasks require proven human-boundedness + a HUMAN.md entry

## Problem

Maintainer directive (Steven, 2026-07-21): "we should not be filing
attended only tasks unless they have specific HUMAN.md tasks associated
with them that could not be done by a machine."

Live failure the same day: the ctx-dispatch-adoption breakdown filed
task 05 (add `Bash(ctx *)` to 8 repos' `.claude/settings.json`) as
MANUAL/attended-only, `Status: blocked` + `Unblock: decide:`. But that
work is fully machine-executable — any session with cwd `~` can edit and
commit those files; the real constraint was drain's Touch contract (a
~/claude worker may not mutate external repos) and unattended-push
safety, not human capability. Filed as attended-only it becomes the
worst of both worlds: no agent will ever do it, and it is invisible to
the human-tasks flow (`/human-tasks` collects HUMAN.md entries, not
task-file prose), so it just sits. This violates the standing
attention-surfacing principle: agent-bounded work always proceeds;
human-bounded work is tracked AND surfaced.

The current /breakdown text institutionalizes the mistake: its
manual-flag rule ("a task whose acceptance commands require launchctl, a
system installer, or interactive OAuth is never drain-completable
unattended — flag such a task MANUAL / human-pending") conflates
"unsafe/impossible UNATTENDED" with "impossible for a MACHINE". Only the
second justifies attended-only; the first calls for structural guards on
an ordinary agent task. And when the second genuinely holds, the
existing HUMAN.md machinery (`.claude/rules/human-blockers.md`) is where
it must surface — breakdown today never files the entry.

## Solution

Make human-boundedness a tested classification in /breakdown with a
mandatory HUMAN.md linkage for the genuinely human-bounded remainder,
and retrofit the existing open attended-only tasks.

## Requirements

- R1 — Boundedness test in /breakdown. Replace the manual-flag rule:
  before marking any task or criterion MANUAL/attended, classify it —
  **human-bounded** means a step a machine cannot perform under ANY
  session shape: credentials/OAuth only the human can complete, a
  purchase or access provision, a physical action, or a decision the
  spec explicitly reserves to the human. Everything else — including
  work that is merely unsafe or out-of-contract for an UNATTENDED
  worker (privileged commands, cross-repo mutation, launchctl) — is
  filed as an ordinary agent task with structural guards stated in its
  headers (blocked-until-lease, an explicit "run from cwd X" step,
  isolation, or a named attended-session dispatch), never as
  attended-only. The rule text names the distinction explicitly
  ("unsafe unattended ≠ impossible for a machine"). Acceptance:
  `grep -q 'human-bounded' .claude/skills/breakdown/SKILL.md` succeeds
  (confirmed 0 today) and the launchctl/OAuth sentence no longer routes
  straight to MANUAL without the test; antigravity mirror
  (`antigravity/.agents/workflows/breakdown.md`) carries the same
  procedure; plugin.json bump per conventions.

- R2 — HUMAN.md linkage is mandatory for the remainder. A task that
  survives R1's test as genuinely human-bounded must, in the same
  commit that files it, add a HUMAN.md agent-filed blocker entry
  (grammar per `.claude/rules/human-blockers.md` — cited, not restated)
  whose source path names the task file and whose `Blocks:` clause
  names what the task gates; the task's `Unblock:` line references the
  HUMAN.md entry. No HUMAN.md entry → the task may not be filed
  attended-only (breakdown's rule states this as a hard gate).
  Acceptance: `grep -q 'HUMAN.md' .claude/skills/breakdown/SKILL.md`
  succeeds in the manual-flag rule's context (confirmed: the file has
  no HUMAN.md mention today); the antigravity mirror matches.

- R3 — Retrofit the open attended-only tasks. Sweep this repo's open
  task files for attended-only markers (`grep -rl 'MANUAL\|attended
  session only\|Unblock: decide' specs/*/tasks/`) and reclassify each
  per R1: machine-doable → rewrite as an agent task with structural
  guards (named case: `specs/ctx-dispatch-adoption/tasks/05` — the
  cross-repo allowlist rollout becomes an agent task specifying a
  home-cwd attended-or-supervised session with per-repo lease checks,
  keeping only the never-drain-dispatchable-from-~/claude guard);
  genuinely human-bounded → file the HUMAN.md entry per R2 in the same
  commit. Acceptance: the sweep command's hit list is enumerated in the
  task's evidence with each hit's disposition; after the retrofit,
  every remaining attended-only task file greps a `HUMAN.md` reference
  in its `Unblock:` line (`grep -L` over the hit list → empty).

## Non-goals

- Changing HUMAN.md's grammar or the /human-tasks skill (the rule file
  owns the grammar; this spec only makes breakdown feed it).
- Relaxing unattended-worker safety limits
  (docs/memory/unattended-worker-tool-limits.md stands; this spec is
  about not mislabeling machine work as human work).
- The drain dispatch contract (headers-only parsing) — R1 works with
  it, not against it.

## Seams

`.claude/skills/breakdown/SKILL.md` is also edited by
specs/ctx-dispatch-adoption task 02 (ctx structure-gathering step —
different section). The two edits land serialized, whichever is second
rebasing on the first. This spec touches no ctx SKILL.md and needs no
slot in the token-doctrine editor registry.

## Evidence

- specs/ctx-dispatch-adoption/tasks/05-repo-allowlist-rollout.md (the
  live mislabeled case, 2026-07-21) and its decomposition-critic finding
  (prose MANUAL guard invisible to drain's header-only dispatch).
- Attention-surfacing principle: agent-bounded proceeds, human-bounded
  is tracked and surfaced (toolkit 0.8.60–0.8.63).

Next stage: /critique specs/attended-task-human-boundedness/SPEC.md
(human-launched), then /breakdown.
