# Task 02: workflow-author both-or-neither stage-tiering rule

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers. -->

Status: done
Depends on: none
Priority: P1
Budget: 5 turns
Spec: ../SPEC.md (requirement R2)
Touch: .claude/skills/workflow-author/

## Goal

The workflow-author skill requires every mechanical stage (search, fetch,
extract, grep-like scouting, conformance checks) in a generated script to
pass BOTH `model` (cheap tier alias) and `effort: 'low'`, and judgment
stages to omit `model` deliberately — with a one-line comment in the
generated script naming which each stage is. The rule lands in an
ALWAYS-APPLIES location (Procedure step 2, or a new subsection OUTSIDE the
"Doctrine guards" block whose preamble scopes to queue-state scripts).
Template/example snippets in the skill directory (including any mechanical
stage in queue-wave/reference examples) updated to carry the pin.

## Touch

workflow-author skill directory only. Do NOT touch deep-research.js
(task 01) or plugin.json (task 03 owns the bump). Do NOT add the rule
under the doctrine-guards queue-state preamble.

## Steps

1. Add the rule at the always-applies location; update example snippets.
2. Confirm placement is outside the queue-state-scoped block.

## Acceptance

- [x] `grep -qi 'model' .claude/skills/workflow-author/SKILL.md` → hits
  (MANUAL: rule states mechanical stages pass model+effort, judgment
  stages inherit deliberately, one-line stage-kind comment required, and
  it sits OUTSIDE the queue-state doctrine-guards preamble)
  — verified: new "## Stage tiering" section at SKILL.md:42 (before
  "## Doctrine guards":62), states both-or-neither + one-line stage-kind
  comment; grep HIT (evidence/02-workflow-author-rule.md)
- [x] `grep -riq 'effort' .claude/skills/workflow-author/` → example
  snippets show model+effort together on a mechanical stage
  — verified: reference.md:168 `model: 'haiku', effort: 'low'` on the
  queue-wave inventory (mechanical) stage; judgment stages carry
  deliberate-omit comments (evidence/02-workflow-author-rule.md)
