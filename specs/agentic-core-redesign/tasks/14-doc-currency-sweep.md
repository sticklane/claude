# Task 14: doc currency sweep — the remaining prose that describes retired mechanisms

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch, Rigor) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Priority values run P0 (highest) through P3; the header is optional — absent means P2. -->
<!-- Status vocabulary: pending → in-progress → done; also blocked (always with an Unblock: line), deferred, skipped, draft (stub awaiting promotion), and needs-verification (implementation complete, acceptance unverified — the verifier flips it to done; scanners treat it as open agent-bounded work, never a needs-attention flag). -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers, in every task file — and ## Progress / ## Deferred questions are drain-written sections (single writer, main checkout): workers report that content, never write it. -->

Status: pending
Depends on: 09, 11, 13
Priority: P2
Budget: 20 turns
Spec: ../SPEC.md (2026-07-22 addendum; "Breakdown requirements" — AGENTS.md and README updates)
Touch: docs/architecture.md, docs/anthropic-playbook.md, docs/external-playbooks.md, docs/decisions/work-tracking.md, docs/memory.md

## Goal

Every doc in `docs/` that describes this repo's own mechanics — not
just the narrow slices tasks 09 (AGENTS.md/README commands), 11
(`docs/human-gates.md`), and 13 (`.claude/rules/`, `CLAUDE.md`)
already own — reads true after the pivot. Concretely:

- `docs/architecture.md` existed before this pivot describing the
  mirror trees, the launch-authorization contracts, and drain's
  baton/lease/generation machinery as current. It was dropped
  uncommitted rather than shipped stale (2026-07-22 sync session) —
  this task writes the real replacement: component architecture,
  pipeline, and runtime-portability sections rewritten for the
  data-level model (bd queue + ctx index + task files; no mirror
  trees), citing `docs/architecture-pivot-2026-07-22.md` for the
  decision rather than restating it.
- `docs/anthropic-playbook.md` and `docs/external-playbooks.md`: any
  passage citing the deleted composer, the custom work loop, or
  procedure-level portability as this repo's practice gets corrected
  or footnoted as superseded, once tasks 09/11/13 land (hence the
  dependency — this task documents the POST-cutover state, not a
  moving target).
- `docs/decisions/work-tracking.md`'s 2026-07-03 "full exit" decision
  ("markdown docs/TASKS.md checkboxes... everywhere", bd fully
  removed) is now reversed for this repo by the 2026-07-22 pivot. Add
  a dated addendum (do not rewrite the historical record) noting the
  reversal and pointing at `specs/beads-daily-skill/SPEC.md` and
  `docs/architecture-pivot-2026-07-22.md`.
- `docs/memory.md`'s index: confirm no entry there describes a
  now-deleted mechanism (mirror procedure discipline, launch
  authorization) as live guidance; add a one-line pointer to the
  pivot doc if the topic recurs.

## Touch

Read-only over everything else. Does not touch AGENTS.md, README.md,
`docs/human-gates.md`, `CLAUDE.md`, or `.claude/rules/` — those are
tasks 09, 11, and 13's Touch.

## Steps

1. Grep `docs/*.md` for the retired-mechanism vocabulary (mirror
   trees/manifest, launch-authorization contract, baton, lease,
   generation counter, composer, `agentic loop`) outside the doc's own
   historical-record framing; list every hit with file:line.
2. For each hit, either correct it (present tense, describes current
   behavior) or mark it explicitly historical (a dated note, not a
   silent leave-as-is) — never delete a decision record's own account
   of what was true when it was written.
3. Write `docs/architecture.md` fresh per the Goal above.
4. Run `/prose-review` over every changed file per CLAUDE.md's
   authoring-conventions bullet (human-facing prose in `docs/*.md` is
   its charter) and fix findings before committing.

## Acceptance

- [ ] `test -f docs/architecture.md && echo EXISTS` → `EXISTS`
- [ ] `grep -c "mirror tree\|mirror manifest\|launch-authorization contract\|drain.*baton\|drain.*lease\|generation counter" docs/architecture.md` → `0` (no retired mechanism described as current in the rewritten file)
- [ ] `grep -n "full exit\|hybrid retired" docs/decisions/work-tracking.md | wc -l` → unchanged from this task's base commit (historical record preserved), AND `grep -c "2026-07-22" docs/decisions/work-tracking.md` → ≥ `1` (addendum present)
- [ ] `bash scripts/check.sh` → green
- [ ] a `/prose-review` pass over the changed files, evidence pasted into this task's Progress section, shows no unresolved findings above low severity

Depth ceiling: L1 — doc accuracy is a human/prose-review read; the
mechanical complement is the grep-based acceptance checks above plus
task 12's audit job, which would surface renewed drift as a filed
issue rather than let it sit silent.
