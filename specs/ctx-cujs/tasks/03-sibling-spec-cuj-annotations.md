# Task 03: sibling specs gain "Serves CUJ" annotations

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch, Rigor) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Priority values run P0 (highest) through P3; the header is optional — absent means P2. -->
<!-- Status vocabulary: pending → in-progress → done; also blocked (always with an Unblock: line), deferred, skipped, draft (stub awaiting promotion), and needs-verification (implementation complete, acceptance unverified — the verifier flips it to done; scanners treat it as open agent-bounded work, never a needs-attention flag). -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers, in every task file — and ## Progress / ## Deferred questions are drain-written sections (single writer, main checkout): workers report that content, never write it. -->

Status: pending
Depends on: none
Priority: P2
Budget: 10 turns
Spec: ../SPEC.md (requirements R4)
Touch: specs/ctx-skill-token-doctrine/SPEC.md, specs/ctx-query-ergonomics/SPEC.md, specs/ctx-static-analysis-augmentation/SPEC.md

## Goal

Each of the three named in-flight sibling specs gains a one-line
"Serves CUJ: <name(s)>" annotation under its title — mechanical, no other
content change. `specs/ctxignore-git-overlay` is explicitly EXCLUDED (it
already shipped). Round-2 specs (ctx-minified-skip, ctx-dead-code-zones,
ctx-absence-check) already carry the line — do not touch them, this task
is only for the three named specs.

## Touch

Only the three SPEC.md files' title/header area (add one line under the
`#` title, same format as the already-annotated round-2 specs — e.g.
`specs/ctx-absence-check/SPEC.md`'s "Serves CUJ: VERIFY ABSENCE
(docs/guides/ctx-cujs.md)."). Do not change anything else in any of the
three files — this is an annotation-only mechanical edit, never a content
change to Problem/Solution/Requirements.

## Steps

1. For each of the three specs, read ../SPEC.md's own Solution section
   (this spec's CUJ list) to find which CUJ(s) cite that sibling spec by
   path — a spec may be cited under more than one CUJ (e.g.
   ctx-query-ergonomics is cited under both CUJ 2 LOCATE and CUJ 3 DIG
   IN; ctx-static-analysis-augmentation is cited under both CUJ 5 IMPACT
   and CUJ 7 DEDUP/DEAD CODE) — list every CUJ that cites it, matching
   the format already used by the round-2 specs' own annotation lines
   (read one of those as a formatting example, e.g.
   `specs/ctx-dead-code-zones/SPEC.md`'s two-CUJ line).
   - ctx-skill-token-doctrine: cited under CUJ 6 SURVEY.
   - ctx-query-ergonomics: cited under CUJ 2 LOCATE and CUJ 3 DIG IN.
   - ctx-static-analysis-augmentation: cited under CUJ 5 IMPACT and
     CUJ 7 DEDUP/DEAD CODE.
2. Add the one-line annotation under each spec's `#` title, matching the
   existing round-2 format (cite `docs/guides/ctx-cujs.md`).
3. Make no other edit to any of the three files.

## Acceptance

- [ ] `grep -l 'Serves CUJ' specs/ctx-skill-token-doctrine/SPEC.md specs/ctx-query-ergonomics/SPEC.md specs/ctx-static-analysis-augmentation/SPEC.md`
      lists all three named files.
- [ ] `git diff --stat` for this task's commit touches only the three
      files listed in Touch — no other spec, no non-header lines beyond
      the one inserted annotation line per file (spot-check the diff is a
      single-line insertion per file).
