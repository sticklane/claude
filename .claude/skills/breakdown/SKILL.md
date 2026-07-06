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

A version-bump acceptance criterion must check "changed from the value at
the task's own base commit" (e.g. `git show <base-commit>:<path> | grep
version` compared against the current value), never a hard-coded exact
pre-task literal — a sibling task landing first can bump the same file, so
a pinned literal false-fails once the on-disk value has already moved past it.

4. Order tasks so each leaves the build green — no task may depend on a later
   one to compile or pass tests. Assign each task's `Priority:` by this
   rubric:
   - P0 — repair or unblocking work: fixes or unblocks files other tasks
     edit, or proves the spec's riskiest assumption.
   - P1 — sits on the longest remaining dependency chain.
   - P2 — the default.
   - P3 — cleanup / nice-to-have.
     The human may re-prioritize at any time by editing the headers.
5. Append a **Parallelization** section to SPEC.md, then emit each
   concurrent-safe group as a machine-readable `- Group:` line under it.
   Apply the **decision-coupling** test before grouping: tasks are
   parallel-safe only if they are disjoint in `Touch` AND free of shared
   undecided design — naming, schema, interface, or architectural choices
   the spec leaves open. If two tasks would each make the same open
   choice, either the choice moves into the spec or the tasks serialize.
   Only groups passing both checks may run concurrently — this step fixes
   the output format, not that judgment call.

   Emit each surviving group as its own line, format
   `- Group: NN, NN[, NN...]` — comma-and-space-separated two-digit task
   numbers matching each task file's `NN-` prefix; a task named on no
   `- Group:` line runs solo. Plain-prose rationale may precede the lines,
   but the lines themselves are the parseable contract: drain parses group
   membership from them rather than re-deriving independence from prose.
   This is the grammar pinned in `specs/drain-rolling-window/SPEC.md`'s
   `## Parallelization` section — cite that paragraph rather than
   re-deriving the format. Example — one line per concurrent-safe group,
   flush-left under the Parallelization heading:

```
- Group: 02, 03
- Group: 05, 06
```
6. Sanity-check with the `critic` agent if the decomposition has any
   nontrivial dependency structure.

## Queue tuning

A drained spec may carry a `Relaunch-every: N` header in its SPEC.md header
block to tune how often /drain hands off via its baton (the self-relaunch
generation budget); absence means the default of 4. The baton grammar itself
lives in drain's reference — cite it, don't restate it here.

## Hand off

Tell the user: run `/build specs/<slug>/tasks/01-*.md` in a fresh session per
task, `/drain specs/<slug>` to work the queue unattended (ask it for
throughput to dispatch independent groups concurrently), or
`/autopilot specs/<slug>/tasks/NN-*.md` for unattended execution of
peripheral tasks (once `/gate` is installed). These next stages are all
launch-gated per the self-chain bullet in CLAUDE.md's authoring conventions,
so /breakdown always ends with this printed pointer, never an invocation.

Close with:
`Next stage: /build specs/<slug>/tasks/01-*.md or /drain specs/<slug>
(human-launched)`.
