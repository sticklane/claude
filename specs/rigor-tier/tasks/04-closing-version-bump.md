# Task 04: version bump + ultra-gate closing check

Status: done
Depends on: 01, 02, 03
Priority: P3
Budget: 4 turns
Spec: ../SPEC.md (requirement R8)
Touch: .claude-plugin/plugin.json

## Goal

`.claude-plugin/plugin.json`'s `version` is bumped, closing out this
spec's mirroring convention (a version bump accompanies any skill-behavior
change). This is the last task so it bumps from whatever the version is
at its own base commit, not a value hard-coded when this task file was
written — tasks 01-03 may have already bumped it, or other unrelated work
may have landed first.

## Touch

Do not touch any SKILL.md or rule file — every other task's edits must
already be merged before this task starts (see Depends on).

## Steps

1. Read the live `.claude-plugin/plugin.json` version right before making
   your commit (not the value stated in SPEC.md — that snapshot has gone
   stale repeatedly during this spec's critique rounds due to concurrent
   merges bumping it; always re-check live).
2. Bump the patch version by one from whatever you just read, and commit.
3. Confirm `bash evals/lint-ultra-gate.sh` still exits 0 (tasks 01 and 02
   touched idea/build/drain; this is a final check that no combination of
   their merged edits broke the gate).

## Acceptance

- [x] `git show HEAD~1:.claude-plugin/plugin.json | grep -o '"version": "[^"]*"'`
      differs from `.claude-plugin/plugin.json`'s current `"version"`
      value, and the current value is a one-patch-level increment above
      it (never a decrease). `HEAD~1` is the commit immediately before
      your own version-bump commit — always resolvable right after you
      make it, unlike a pre-stated literal pin.
      Evidence: HEAD~1 = "version": "0.9.14", current = "version": "0.9.15" (one-patch increment).
- [x] `bash evals/lint-ultra-gate.sh` exits 0
      Evidence: "lint-ultra-gate: OK — all ultra mentions gated in 4 files", exit 0.
