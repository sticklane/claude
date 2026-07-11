# Task 01: gen-1 hub-economics advisory block in drain SKILL.md

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers. -->

Status: pending
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
- [ ] `wc -l < .claude/skills/drain/SKILL.md` → still < 500
