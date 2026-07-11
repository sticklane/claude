# Task 01: gen-1 hub-economics advisory block in drain SKILL.md

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers. -->

Status: in-progress
Depends on: none
Priority: P1
Budget: 4 turns
Spec: ../SPEC.md (requirements R1, R2)
Touch: .claude/skills/drain/SKILL.md

## Goal

Drain SKILL.md step 1 gains a block titled exactly "Hub-economics
advisory" (beside the shell-naming and session-sweep startup steps) with
two advisory lines, gen-1 only, never blocking: (a) frontier-hub — when
the model name the harness disclosed in the session's system context maps
to frontier tier via runtimes/ language (Claude default: fable), print
one line citing the wake-economics doctrine and recommending a deep-tier
(opus) or lower hub via fresh-session relaunch with the same /drain
argument (queue state is committed, nothing lost); skip where the runtime
discloses no model. (b) heavy-hub — when the drain launch arrives beyond
the session's first few turns (the stated observable heuristic), print
one line recommending the same fresh-session relaunch. Neither line ever
blocks dispatch or prints on baton generations.

## Touch

One file. Do NOT touch antigravity/ or plugin.json (task 02 owns both);
do NOT edit the wake-economics doctrine text itself (drain-wake-cost owns
it — this block cites it).

## Steps

1. Add the block; keep it within step 1's startup area, tight prose.
2. Verify the marker grep and that SKILL.md stays under the 500-line
   convention.

## Acceptance

- [ ] `grep -qi 'hub-economics advisory' .claude/skills/drain/SKILL.md` → hits
- [ ] MANUAL: block covers both advisories, gen-1 only, non-blocking,
  names the disclosed-model signal and the beyond-first-few-turns
  heuristic, recommends the deep-tier fresh-session relaunch
## Deferred questions

- [2026-07-11 /drain gen3] Acceptance criterion 3 (`wc -l
  .claude/skills/drain/SKILL.md` → still < 500) is unsatisfiable as
  written: the file is ALREADY 561 lines before this task, and this task
  only adds a "Hub-economics advisory" block (growing it further). The
  task's Touch is the single file `.claude/skills/drain/SKILL.md`, so
  there is no in-scope path to drop below 500 without deleting load-bearing
  procedure (and the wake-economics doctrine text is explicitly off-limits;
  `reference.md` is outside Touch, so content cannot be extracted there
  within scope). Human decision needed — pick one: (a) drop/relax
  criterion 3 (accept that drain SKILL.md already exceeds the 500-line
  convention and this task is not the vehicle to fix it — the advisory
  block is small); or (b) authorize a companion refactor task that extracts
  drain SKILL.md body content into `reference.md` to get under 500,
  widening Touch accordingly, sequenced before or alongside this task.
  Blocking: criteria 1 (marker grep) and 2 (manual coverage) are
  satisfiable now; only criterion 3 blocks DONE. Task 02 (mirror-and-bump)
  depends on this task, so the whole drain-hub-economics spec is stalled
  until this is resolved.


## Answers

- [2026-07-11, Steven via interview] Criterion 3 (<500 lines) RELAXED —
  removed from acceptance (option a). drain SKILL.md already exceeded the
  convention (561 lines) before this task; the advisory block lands anyway.
  The extraction back under 500 is tracked by the EXISTING draft
  specs/drain-wake-cost/tasks/04-skill-length-drift.md — do not create a
  duplicate stub, and do not attempt the extraction in this task.
