# Task 04: Mandatory criteria-adequacy line in the verifier verdict

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch, Rigor) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. -->

Status: pending
Depends on: 01
Priority: P2
Budget: 6 turns
Spec: ../SPEC.md (requirement R5)
Touch: .claude/agents/verifier.md

## Goal

verifier.md's verdict format carries a mandatory criteria-adequacy line:
per requirement, do the passing criteria entail it; any behavioral
requirement whose only green evidence is L0 is INCOMPLETE, not PASS —
with the two decided carve-outs verbatim from R5: ceiling-annotated
prose requirements are exempt, and done/archived work is exempt
unconditionally (ladder levels reported informationally only; binding
scope is the NOT-done + ladder-marker self-detection rule).

## Steps

1. Read task 01's doctrine section and verifier.md's verdict format.
2. Add the criteria-adequacy line spec to the verdict template, citing
   the memory doc for the ladder; encode both carve-outs exactly as R5
   states them — the INCOMPLETE rule must not fire on grandfathered
   done work.

## Acceptance

- [ ] `grep -c 'criteria-adequacy' .claude/agents/verifier.md` → ≥ 1
      (0 today, verified 2026-07-19). Depth ceiling: prose charter —
      behavioral complement is a manual-pending human read of the first
      post-change verifier verdict, confirming the line appears per
      requirement and is non-vacuous.
