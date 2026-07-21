# Task 01: Re-triage the open queue against the agentic design

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch, Rigor) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Priority values run P0 (highest) through P3; the header is optional — absent means P2. -->
<!-- Status vocabulary: pending → in-progress → done; also blocked (always with an Unblock: line), deferred, skipped, draft (stub awaiting promotion), and needs-verification (implementation complete, acceptance unverified — the verifier flips it to done; scanners treat it as open agent-bounded work, never a needs-attention flag). -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers, in every task file — and ## Progress / ## Deferred questions are drain-written sections (single writer, main checkout): workers report that content, never write it. -->

Status: pending
Depends on: none
Priority: P1
Budget: 16 turns
Spec: ../SPEC.md (Migration step 1)
Touch: specs/

## Goal

Every open item in the repo's queue — each task with Status
pending/blocked/deferred/draft and each spec with no tasks/ directory —
carries a triage verdict against this design: `keep` (still valid work),
`subsumed` (the redesign replaces it; task marked obsolete), or
`fold-in` (its content belongs in an agentic-core-redesign task). The
verdicts live in `specs/agentic-core-redesign/TRIAGE.md`, and subsumed
items' Status headers are flipped to `obsolete` in the same commit so no
drain ever dispatches them.

## Touch

The `Touch:` header is the whole `specs/` tree because triage edits
headers across many specs; the bounds in this section are the real
scope. Header-line edits (`Status:`) on other specs' task files are in
scope ONLY for items triaged `subsumed`. Do not edit any body text of other
specs' files. Do not touch `specs/agentic-core-redesign/tasks/` beyond
this file's own checkboxes.

## Steps

1. Enumerate open items with the cheap tools: `grep -l '^Status: \(pending\|blocked\|deferred\|draft\)' specs/*/tasks/*.md` and list `specs/*/` dirs lacking `tasks/`.
2. For each, read only the header + Goal (head -n 30), judge against SPEC.md's design decisions and migration steps, and record `<path> · keep|subsumed|fold-in · <one-line reason>` in TRIAGE.md. The spec pre-names three subsumed clusters (mirror machinery, drain self-patch, ctx-dispatch-adoption prompt-stanza tasks) — verify membership rather than assuming it.
3. Flip subsumed items to `Status: obsolete`, citing TRIAGE.md on the line below.
4. For fold-in items, add the fold target (which agentic task absorbs it) to TRIAGE.md.

## Acceptance

- [ ] `bash -c 'open=$(grep -l "^Status: \(pending\|blocked\|deferred\|draft\)" specs/*/tasks/*.md | grep -v agentic-core-redesign | wc -l); rows=$(grep -c "· \(keep\|subsumed\|fold-in\) ·" specs/agentic-core-redesign/TRIAGE.md); [ "$rows" -ge "$open" ] && echo COVERED'` → prints `COVERED` (every open item has a triage row; specs without tasks/ add rows beyond the minimum)
- [ ] `bash -c 'for f in $(grep "· subsumed ·" specs/agentic-core-redesign/TRIAGE.md | cut -d" " -f1); do case "$f" in specs/*/tasks/*.md) grep -q "^Status: obsolete" "$f" || echo "not flipped: $f";; esac; done'` → no output (every subsumed task file is flipped)

Depth ceiling: L1 — triage verdicts are human judgments over prose; the
behavioral complement is a maintainer read of TRIAGE.md before drain runs
on the remaining queue.
