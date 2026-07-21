# Task 04: plugin.json version bump (closing)

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch, Rigor) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Priority values run P0 (highest) through P3; the header is optional — absent means P2. -->
<!-- Status vocabulary: pending → in-progress → done; also blocked (always with an Unblock: line), deferred, skipped, draft (stub awaiting promotion), and needs-verification (implementation complete, acceptance unverified — the verifier flips it to done; scanners treat it as open agent-bounded work, never a needs-attention flag). -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers, in every task file — and ## Progress / ## Deferred questions are drain-written sections (single writer, main checkout): workers report that content, never write it. -->

Status: done
Depends on: 01, 02, 03
Priority: P3
Budget: 6 turns
Spec: ../SPEC.md (requirements R7)
Touch: .claude-plugin/plugin.json

## Goal

`.claude-plugin/plugin.json`'s `version` is bumped, reflecting this
spec's completed skill-behavior changes (the closing task — depends on
01-03 so the bump happens once, after everything else has landed).

## Touch

Only the `version` field in `.claude-plugin/plugin.json`. Do not touch
any other field or file.

## Steps

1. Read the current `version` value.
2. Bump the patch component by 1 (semver: `X.Y.Z` → `X.Y.(Z+1)`) unless
   the repo's own convention (check recent `git log -p -- .claude-plugin/plugin.json`
   for the last few bumps) indicates a different component — match
   whatever pattern recent bumps actually used.

## Acceptance

- [x] `base=$(git merge-base HEAD main); git show "$base":.claude-plugin/plugin.json | grep '"version"'`
      vs. `grep '"version"' .claude-plugin/plugin.json` (current) — the
      two values differ (confirms this task's own commit changed it, not
      unrelated drift). Evidence: base `0.9.29`, current `0.9.30`.
- [x] The current value's dotted-integer parse
      (`grep -oE '[0-9]+\.[0-9]+\.[0-9]+' .claude-plugin/plugin.json`,
      split on `.`) is greater than the base value's, compared
      component-by-component as integers (confirms a real bump, not a
      revert or typo — e.g. `0.9.30 > 0.9.29` holds, `0.9.3 > 0.9.29`
      does not by string comparison, must compare as integers). Evidence:
      0=0, 9=9, 30>29 — greater, patch-bump convention matched (last 5
      bumps were all patch increments).
