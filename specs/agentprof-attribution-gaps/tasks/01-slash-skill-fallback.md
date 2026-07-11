# Task 01: skill frame fallback from <command-name> tags

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers. -->

Status: pending
Depends on: none
Priority: P1
Budget: 8 turns
Spec: ../SPEC.md (requirement R1)
Touch: agentprof/internal/claude/, agentprof/testdata/

## Goal

When a transcript line carries no `attributionSkill` and the turn's
opening user message contains `<command-name>/x</command-name>`, samples
in that turn get frame `skill:x` (plugin namespace stripped, same
normalization as `normalizeSkillFrame`). Harness builtins that are not
skills (`/clear`, `/model`, `/reload-plugins`, `/rate-limit-options`) map
to `(no skill)` via a builtin denylist. A present `attributionSkill`
always wins. Feasible path per critique: `turnPrompt` (claude.go:~647)
already extracts the command; store it on `turnRec` (claude.go:~408) and
consult it at sample-emit time.

## Touch

`internal/claude/` only. Tasks 02/03/04 edit the same file afterwards —
this task is the head of the serial chain; keep the diff scoped to the
skill-frame decision.

## Steps

1. Failing tests first: fixture turns for (a) `<command-name>/parallel`
   with no attributionSkill → `skill:parallel`; (b) `/clear` turn →
   `(no skill)`; (c) attributionSkill present + tag present →
   attributionSkill wins; (d) namespaced `/agentic:drain` tag →
   `skill:drain`.
2. Store the extracted command on the open turn record; fall back at
   emission.

## Acceptance

- [ ] `cd agentprof && go test ./internal/claude/` → pass including the
  four fixture cases above
- [ ] `bash agentprof/scripts/check.sh` → green
