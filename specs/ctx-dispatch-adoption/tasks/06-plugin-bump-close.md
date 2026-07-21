# Task 06: closing plugin.json bump + mirror sweep

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch, Rigor) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Priority values run P0 (highest) through P3; the header is optional — absent means P2. -->
<!-- Status vocabulary: pending → in-progress → done; also blocked (always with an Unblock: line), deferred, skipped, draft (stub awaiting promotion), and needs-verification (implementation complete, acceptance unverified — the verifier flips it to done; scanners treat it as open agent-bounded work, never a needs-attention flag). -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers, in every task file — and ## Progress / ## Deferred questions are drain-written sections (single writer, main checkout): workers report that content, never write it. -->

Status: pending
Depends on: 01, 02, 03
Priority: P2
Budget: 4 turns
Spec: ../SPEC.md (closing obligation per CLAUDE.md authoring conventions)
Touch: .claude-plugin/plugin.json

## Goal

The plugin version reflects the skill-behavior changes tasks 01–03
shipped (drain/build/breakdown/onboard skill edits + critic agent
change), in one closing bump — the CLAUDE.md "typically one closing
task" pattern, avoiding three tasks contending on plugin.json.

## Steps

1. Confirm tasks 01, 02, 03 are `Status: done`.
2. Bump `version` in `.claude-plugin/plugin.json` (patch bump). The
   critic agent is enumerated in plugin.json — verify its entry needs no
   change beyond the version (tools frontmatter lives in the agent file,
   not the manifest); adjust the manifest only if task 01–03 changes
   made an enumerated field stale.
3. Run the mirror-verification closure sweep over the mirrors tasks
   01–03 touched (`.claude/rules/mirror-verification.md`: closure-
   triggered cross-reference check — do the mirrors' paths/commands
   still resolve under their runtimes).

## Acceptance

- [ ] `git show $(git merge-base HEAD origin/main):.claude-plugin/plugin.json | grep '"version"'` differs from `grep '"version"' .claude-plugin/plugin.json` (changed from this task's own base commit — never a hard-coded literal; a sibling spec may bump concurrently)
- [ ] `python3 -c "import json; json.load(open('.claude-plugin/plugin.json'))"` → exit 0
- [ ] `bash tests/test_mirror_procedure_coverage.sh` → exit 0

Depth ceiling: L1 — a version bump has no deeper runnable check; the
mirror sweep is the closure-triggered manual/agent read
mirror-verification.md prescribes.
