# Task 02: Drain SKILL.md and reference.md consume the scanner

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch, Rigor) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. -->

Status: done
Depends on: 01
Priority: P1
Budget: 10 turns
Spec: ../SPEC.md (requirement R3)
Touch: .claude/skills/drain/SKILL.md, .claude/skills/drain/reference.md

## Goal

Every point where the frontier is currently model-derived defers to the
scanner: the inventory step invokes `drain_frontier.py` per spec dir;
step 2's tie-break paragraph carries the mandated verbatim sentence
"tie-break is computed by drain_frontier"; reference.md's Rolling-window
admission section defers to scanner output for structure while drain
keeps the live-window gate and admit count. The fallback is explicit:
script missing or non-zero → today's header-reading procedure verbatim,
with scanner stderr quoted in the fallback log line.

## Touch

Do NOT touch the mirrors (task 04) or evals/ (task 03). Keep additions
minimal — drain/SKILL.md already exceeds the size budget (a separate
spec owns that overage); do not restructure unrelated sections.

## Steps

1. Read SPEC.md R3, then the three target regions (inventory step,
   step 2 tie-break, reference.md Rolling-window admission).
2. Edit each to defer to the scanner per R3, including the verbatim
   tie-break sentence and the stderr-quoting fallback.
3. drain/SKILL.md is ultra-gated: run `bash evals/lint-ultra-gate.sh`
   before committing.

## Acceptance

- [x] `grep -c 'drain_frontier' .claude/skills/drain/SKILL.md` → ≥ 2
      and `grep -c 'tie-break is computed by drain_frontier'
    .claude/skills/drain/SKILL.md` → ≥ 1 and `grep -c
    'drain_frontier' .claude/skills/drain/reference.md` → ≥ 1 (all
      anchors 0 today, verified 2026-07-19). Depth ceiling: procedure
      prose — behavioral complement is task 03's trajectory assertion
      plus task 01's unit tests.
      Evidence: counts 2 / 1 / 1 observed; verifier PASS
      (evidence/02-drain-consumes-scanner.md).
- [x] `bash evals/lint-ultra-gate.sh` → exit 0
      Evidence: exit 0, "all ultra mentions gated in 4 files"; size gate
      also green at exactly 500 lines (evidence/02-drain-consumes-scanner.md).

## Progress

- [2026-07-20 /drain] Attempt 1 (opus): implementation DONE, verifier PASS
  on all acceptance criteria and mirror-coverage gate, but the merge failed
  drain's own project gate: `bash evals/lint-skill-size-gate.sh` →
  ".claude/skills/drain/SKILL.md:515: exceeds 500-line SKILL.md budget"
  (515 lines, 15 over the 500-line cap; the task added 27 net lines to
  SKILL.md). Branch task/02-drain-consumes-scanner discarded (merge reset,
  never pushed). Relaunching one tier up per the slot machine.
