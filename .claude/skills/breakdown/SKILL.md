---
name: breakdown
description: Decomposes a SPEC.md into independent task files sized for one clean agent session each, with per-task acceptance commands and a parallelization map. Use after a spec is written, when the user wants a spec split into tasks, or asks how to divide work across sessions or agents.
argument-hint: "[path/to/SPEC.md]"
---

Decompose the spec at $ARGUMENTS (if empty: the most recently modified
`specs/*/SPEC.md`, or ask) into task files under the spec's directory, each
executable by a fresh session with no other context.

## Sizing rule

One task = one session = one reviewable commit. If you can't describe a
task's diff in a paragraph, split it. If a task is a one-sentence diff, merge
it into a neighbor. Most specs yield 2–6 tasks; don't manufacture granularity.
Set each task's `Budget:` at roughly 2× the honest turn estimate — it's a
stop line, not a target; workers stop over budget rather than grind. Write
it exactly as `Budget: <N> turns` (integer N — no ranges, no prose):
dispatchers parse it for the over-budget stop and headless `--max-turns`.

## Procedure

1. Read the spec. If anything under Open questions is unresolved, stop and
   say so — decomposing an ambiguous spec multiplies the ambiguity.
2. If file-level dependencies are unclear, ask `scout` agents — don't read
   the codebase into this session.
3. Write `specs/<slug>/tasks/NN-<slug>.md` for each task:

```markdown
# Task NN: <title>

Status: pending
Depends on: <task numbers, or "none">
Budget: <N> turns
Spec: ../SPEC.md (requirements R2, R3)

## Goal
What exists when this task is done, in 2–4 sentences.

## Touch
Files/modules this task may change. Anything else is scope creep.

## Steps
Numbered, concrete. Include "write the failing test first" where the
acceptance criteria are test-shaped.

## Acceptance
Runnable commands only:
- [ ] `<command>` → <expected result>
```

4. Order tasks so each leaves the build green — no task may depend on a later
   one to compile or pass tests.
5. Append a **Parallelization** section to SPEC.md: groups of tasks with
   disjoint `Touch` lists and no dependency edges. Only these may run
   concurrently.
6. Sanity-check with the `critic` agent if the decomposition has any
   nontrivial dependency structure.

## Hand off

Tell the user: run `/build specs/<slug>/tasks/01-*.md` in a fresh session per
task, `/parallel specs/<slug>` to dispatch an independent group at once, or
`/autopilot specs/<slug>/tasks/NN-*.md` for unattended execution of
peripheral tasks (once `/gate` is installed).
