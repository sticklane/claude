# Task 03: Doctrine updates — fleet-sizing citation and research quotes

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Priority values run P0 (highest) through P3; the header is optional — absent means P2. -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers, in every task file — and ## Progress / ## Deferred questions are drain-written sections (single writer, main checkout): workers report that content, never write it. -->

Status: pending
Depends on: none
Priority: P3
Budget: 8 turns
Spec: ../SPEC.md (requirement R6)
Touch: .claude/rules/token-discipline.md, docs/external-playbooks.md

## Goal

`.claude/rules/token-discipline.md`'s fleet-sizing guidance (currently in
"## Delegation defaults": "size it by the task map, never a default
maximum") now cites the 3–5 concurrent-writer window and rolling top-up
that /drain implements per specs/drain-rolling-window, instead of only
the generic "multi-agent work costs ~15×" framing. `docs/
external-playbooks.md` gains the verbatim research quotes that spec's
"Research grounding" section cites (agent-teams shared task list,
3–5-teammate sweet spot, file-ownership-per-teammate, serial integration
across every lab, Cognition's shared-contract warning), so skills cite
that file rather than restating the quotes inline.

## Touch

In scope: the fleet-sizing bullet(s) in token-discipline.md's "##
Delegation defaults" (and, only if directly relevant, "## Dispatch
authoring") section; a new or extended entry in docs/
external-playbooks.md carrying the research quotes.

Out of scope: any other rule in `.claude/rules/`, and
docs/anthropic-playbook.md (a different, pre-existing doctrine file —
this task does not touch it).

## Steps

1. Read `.claude/rules/token-discipline.md`'s "## Delegation defaults"
   section and `docs/external-playbooks.md`'s existing structure (so the
   new entry matches its citation style) before editing.
2. In token-discipline.md, extend the fleet-sizing bullet to name the
   3–5 concurrent-writer sweet spot and drain's rolling top-up (verdict-
   triggered refill, not wave-barrier refill) as the standing guidance
   for when a task map genuinely supports concurrency — cite
   docs/external-playbooks.md for the research, don't restate the quotes
   here.
3. In docs/external-playbooks.md, add the verbatim quotes from
   specs/drain-rolling-window/SPEC.md's "Research grounding" section:
   the agent-teams shared-task-list quote, the 3–5-teammate sweet-spot
   quote, the file-ownership-per-teammate quote, the serial-integration-
   everywhere observation, and Cognition's shared-contract warning — each
   with its source citation, matching the file's existing per-entry
   format.
4. Cross-check that neither edit contradicts token-discipline.md's
   existing "One worker is the default" framing — the new text tightens
   sizing guidance, it does not change the opt-in default.

## Acceptance

- [ ] `grep -ci '3.5\|3–5\|3-5' .claude/rules/token-discipline.md` → ≥ 1
- [ ] `grep -ci 'rolling top.up\|rolling top-up' .claude/rules/token-discipline.md`
      → ≥ 1
- [ ] `grep -ci 'agent teams\|agent-teams' docs/external-playbooks.md`
      → ≥ 1
- [ ] `grep -ci 'shared.contract\|shared contract' docs/external-playbooks.md`
      → ≥ 1
