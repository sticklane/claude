# Task 01: pin haiku on deep-research Search/Fetch stages

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers. -->

Status: pending
Depends on: none
Priority: P1
Budget: 4 turns
Spec: ../SPEC.md (requirement R1)
Touch: .claude/workflows/deep-research.js

## Goal

Every `agent()` call in deep-research.js's Search (≈line 184-185) and
Fetch/Extract (≈line 215-219) phases passes `model: "haiku"` alongside the
existing `effort: "low"`. Scope, Verify, and Synthesize calls keep
inheriting the session model — no `model` opt, no effort downgrade
(Verify's refuters are judgment per the spec's resolved open question;
record that decision in the file header comment). Phase metadata and
comments that say "effort:low" now say "haiku + effort:low".

## Touch

One file. Do NOT touch the workflow-author skill (task 02) or plugin.json
(task 03 owns the bump; this file is not plugin-distributed).

## Steps

1. Add `model: "haiku"` to the Search and Fetch/Extract `agent()` opts;
   update the `meta.phases` detail strings and stage comments.
2. Add the Verify-is-judgment decision line to the header comment block.
3. `node --check` the file.

## Acceptance

- [ ] `node --check .claude/workflows/deep-research.js` → exits 0
- [ ] `grep -n 'model' .claude/workflows/deep-research.js` → hits inside the Search and Fetch agent() opts (MANUAL: confirm Verify/Synthesize/Scope agent() calls carry no model opt)
- [ ] `grep -c 'model: "haiku"' .claude/workflows/deep-research.js` → ≥2
