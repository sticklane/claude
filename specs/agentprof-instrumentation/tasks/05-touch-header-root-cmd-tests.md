# Task 05: Memory note — root-level cmd tests assert fixture sample counts (Touch authoring)

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers. -->

Status: done
Depends on: none
Priority: P3
Budget: 4 turns
Spec: ../SPEC.md
Discovered-from: 01-tool-and-model-durations.md
Touch: docs/memory.md, docs/memory/touch-root-fixture-tests.md

## Goal

The lesson from task 01 is captured as a `docs/memory/` topic note, NOT
as a breakdown-skill edit (destination pinned deliberately: a
`.claude/skills/` edit would owe an antigravity mirror + plugin bump this
task does not carry): tasks that change parser fixtures must list the
root-level test files asserting fixture sample counts (e.g.
`agentprof/cmd_claude_test.go`) in `Touch:` rather than leaving them
implicit — task 01 was mechanically forced outside its declared Touch by
exactly this.

## Steps

1. Write `docs/memory/touch-root-fixture-tests.md` (short topic note:
   the incident, the rule, the example file).
2. Index it in `docs/memory.md` per that file's existing pattern.

## Acceptance

- [x] `test -f docs/memory/touch-root-fixture-tests.md && grep -q 'cmd_claude_test' docs/memory/touch-root-fixture-tests.md` → pass
      Evidence: verifier ran the command → PASS (file exists, `cmd_claude_test` matched); see evidence/05-touch-header-root-cmd-tests.md.
- [x] `grep -q 'touch-root-fixture-tests' docs/memory.md` → match (indexed)
      Evidence: verifier confirmed match at docs/memory.md:15, index line follows the existing pattern.
- [x] `grep -qi 'sample count' docs/memory/touch-root-fixture-tests.md` → match
      Evidence: verifier confirmed match in the note's "The rule" section.
