---
name: breakdown
description: Decomposes a SPEC.md into independent task files sized for one clean conversation each, with per-task acceptance commands and a parallelization map. Use after a spec is written, when the user wants a spec split into tasks, or asks how to divide work across sessions or agents.
---

Decompose the spec (the given path; if none, the most recently modified
`specs/*/SPEC.md`, or ask) into task files under the spec's directory, each
executable by a fresh conversation with no other context.

## Sizing rule

One task = one conversation = one reviewable commit. If you can't describe
a task's diff in a paragraph, split it. If a task is a one-sentence diff,
merge it into a neighbor. Most specs yield 2–6 tasks.
Set each task's `Budget:` at roughly 2× the honest turn estimate — it's a
stop line, not a target; workers stop over budget rather than grind. Write
it exactly as `Budget: <N> turns` (integer N — no ranges, no prose):
dispatchers parse it for the over-budget stop and headless `--max-turns`.

## Procedure

1. Read the spec. If anything under Open questions is unresolved, stop and
   say so — decomposing an ambiguous spec multiplies the ambiguity.
2. If file-level dependencies are unclear, use the scout skill — don't read
   the tree into this conversation.
3. Write `specs/<slug>/tasks/NN-<slug>.md` for each task:

```markdown
# Task NN: <title>

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Priority values run P0 (highest) through P3; the header is optional — absent means P2. -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers, in every task file — and ## Progress / ## Deferred questions are drain-written sections (single writer, main checkout): workers report that content, never write it. -->

Status: pending
Depends on: <task numbers, or "none">
Priority: P2
Budget: <N> turns
Spec: ../SPEC.md (requirements R2, R3)
Touch: <comma-separated paths this task may change>

## Goal

What exists when this task is done, in 2–4 sentences.

## Touch

Optional prose on boundaries (why a path is in or out). When overlap with
a sibling task is plausible, list the adjacent files/modules this task
must NOT touch. Dispatchers parse the `Touch:` header line above, not
this section; anything not listed there is scope creep.

## Steps

Numbered, concrete. Include "write the failing test first" where the
acceptance criteria are test-shaped.

## Acceptance

Runnable commands only:

- [ ] `<command>` → <expected result>
```

For a task whose `Touch:` includes `antigravity/` mirror paths, check
docs/memory/workboard-mirror-verbatim.md before writing the check: only
workboard's two `.py` files are byte-identical across trees — prose-skill
mirrors (`.claude/skills/*/SKILL.md` ↔ `antigravity/.agents/workflows/*.md`
or `.agents/skills/*/SKILL.md`) are paraphrased ports, so a `diff → no
output` criterion will wrongly fail (or force destroying deliberately
hand-adapted wording); write a content-coverage check instead (e.g. grep
for the concepts/identifiers that must land).

4. Order tasks so each leaves the build green — no task may depend on a
   later one to compile or pass tests. Assign each task's `Priority:` by
   this rubric:
   - P0 — repair or unblocking work: fixes or unblocks files other tasks
     edit, or proves the spec's riskiest assumption.
   - P1 — sits on the longest remaining dependency chain.
   - P2 — the default.
   - P3 — cleanup / nice-to-have.
     The human may re-prioritize at any time by editing the headers.
5. Append a **Parallelization** section to SPEC.md: groups of tasks with
   disjoint `Touch` lists and no dependency edges. Apply the
   "decision coupling" test before grouping: tasks are parallel-safe
   only if they are disjoint in Touch AND free of shared undecided
   design — naming, schema, interface, or architectural choices the
   spec leaves open. If two tasks would each make the same open choice,
   either the choice moves into the spec or the tasks serialize. Only
   groups passing both checks may run concurrently.
6. Sanity-check with the critic skill if the decomposition has nontrivial
   dependency structure.

## Queue tuning

A drained spec may carry a `Relaunch-every: N` header in its SPEC.md header
block to tune how often the drain workflow hands off via its baton (the
self-relaunch generation budget); absence means the default of 4. The baton
grammar itself lives in drain's reference — cite it, don't restate it here.

## Hand off

Tell the user: run `/build specs/<slug>/tasks/01-*.md` in a new conversation
per task, or apply the drain workflow (`.agents/workflows/drain.md`) to work
the queue — its group throughput mode hands you concurrent Agent Manager
launches for an independent group.
