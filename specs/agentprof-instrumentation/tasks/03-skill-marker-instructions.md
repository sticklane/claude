# Task 03: Marker-emitting instructions in drain/build skill text + mirrors + plugin bump

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers, in every task file — and ## Progress / ## Deferred questions are drain-written sections (single writer, main checkout): workers report that content, never write it. -->

Status: in-progress
Depends on: none
Priority: P2
Budget: 12 turns
Spec: ../SPEC.md (requirements R4, R5, R8)
Touch: .claude/skills/drain/SKILL.md, .claude/skills/build/SKILL.md, antigravity/.agents/workflows/drain.md, antigravity/.agents/workflows/build.md, .claude-plugin/plugin.json

## Goal

`drain/SKILL.md` carries five distinct hardcoded role-marker instructions —
attempt-1 in step 2 (Dispatch, governing both attempt-1 launch paths with
the same `worker-attempt1` value), and relaunch + three tournament entrants
each at its own call site in step 3 (~`SKILL.md:208` and `:218-222`, line
refs approximate) — each naming its literal
`<!-- agentprof:role=<role> -->` line to prepend to that dispatch's prompt.
Both `drain/SKILL.md` and `build/SKILL.md` instruct each of their five
top-level steps to open with its matching
`<!-- agentprof:stage=<name> -->` line EVERY time the step is entered
(drain's step 2/3 loop re-fires markers per iteration — required, per
SPEC.md). The antigravity mirrors carry the equivalent instructions in the
same commit, and `.claude-plugin/plugin.json`'s version is bumped.

## Touch

`reference.md`'s shared worker-prompt body (~`reference.md:245`) is NOT
edited — it is reused verbatim across dispatch variants and cannot
distinguish roles. Mirrors are paraphrased ports
(docs/memory/workboard-mirror-verbatim.md): port the instructions in the
mirror's own voice, but the marker LITERALS themselves
(`<!-- agentprof:role=... -->` / `<!-- agentprof:stage=... -->`) must appear
exactly, since they are the parser's detection patterns. If the mirror
genuinely lacks an analogous dispatch-prompt construction site, record a
reviewed carve-out as evidence — never a silent skip (R8).

**Serialize:** dispatch this task only when no other live session/drain has
`.claude/skills/drain/SKILL.md` or `.claude/skills/build/SKILL.md` modified
or in-flight (they were being edited by a live drain on 2026-07-06), and
resolve `plugin.json`'s version bump against the file's CURRENT value at
execution time (other specs also bump it — known contention point).

## Steps

1. drain step 2 (Dispatch): add the attempt-1 instruction with literal
   `<!-- agentprof:role=worker-attempt1 -->`, covering both the
   single-worker and concurrent group-throughput launch paths.
2. drain step 3 (Collect the verdict): add the relaunch instruction
   (`worker-relaunch`) at the relaunch call site and one instruction per
   tournament entrant (`worker-tournament-t1`/`-t2`/`-t3`) at the three
   entrant call sites — four separate additions, not a bundle.
3. drain: add the five stage-marker opening instructions
   (`inventory`, `dispatch`, `collect-verdict`, `baton-pass` on the `## 3a`
   subsection, `batch-interview`), each firing on every entry.
4. build: add the five stage-marker opening instructions (`load`, `plan`,
   `implement`, `verify`, `close-out`).
5. Port the equivalent instructions into
   `antigravity/.agents/workflows/drain.md` and `build.md`; bump
   `.claude-plugin/plugin.json` version.
6. Run the ultra-gate lint (drain and build are ultra-path skills) before
   committing.

## Acceptance

- [ ] `grep -c 'agentprof:role=' .claude/skills/drain/SKILL.md` → 5 (R4).
- [ ] `grep -c 'agentprof:stage=' .claude/skills/drain/SKILL.md` → 5 and
      `grep -c 'agentprof:stage=' .claude/skills/build/SKILL.md` → 5 (R5).
- [ ] `grep -c 'agentprof:role=' antigravity/.agents/workflows/drain.md` → 5,
      `grep -c 'agentprof:stage=' antigravity/.agents/workflows/drain.md` → 5,
      `grep -c 'agentprof:stage=' antigravity/.agents/workflows/build.md` → 5
      — OR the task's evidence records an explicit reviewed carve-out for
      the mirror (R8).
- [ ] `git diff HEAD~1 -- .claude-plugin/plugin.json | grep '"version"'`
      shows the version increased (R8).
- [ ] `bash evals/lint-ultra-gate.sh` → pass.
