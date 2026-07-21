# Task 02: sweep for other vague plugin-cache-path phrasings

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch, Rigor) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Priority values run P0 (highest) through P3; the header is optional — absent means P2. -->
<!-- Status vocabulary: pending → in-progress → done; also blocked (always with an Unblock: line), deferred, skipped, draft (stub awaiting promotion), and needs-verification (implementation complete, acceptance unverified — the verifier flips it to done; scanners treat it as open agent-bounded work, never a needs-attention flag). -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers, in every task file — and ## Progress / ## Deferred questions are drain-written sections (single writer, main checkout): workers report that content, never write it. -->

Status: pending
Depends on: 01
Priority: P2
Budget: 12 turns
Spec: ../SPEC.md (requirements R4)
Touch: .claude/skills/_/SKILL.md, .claude/skills/_/reference.md

## Goal

Every other `"resolved at dispatch"` / `"plugin cache path"` phrasing
across `.claude/skills/*/SKILL.md` and `.claude/skills/*/reference.md`
(other than task 01's own canonical recipe section) is repointed at that
canonical recipe by citation, rather than left as its own vague phrasing.

## Touch

Do not edit `.claude/skills/drain/reference.md`'s canonical recipe section
itself (task 01's output) beyond adding citations elsewhere that point at
it. Do not touch `antigravity/` or `codex/` mirror files — that's task 03,
and this sweep is explicitly scoped to `.claude/skills/*` only per the
spec's Solution step 3.

## Steps

1. `grep -rn "resolved at dispatch\|plugin cache path" .claude/skills/*/SKILL.md .claude/skills/*/reference.md`
   to find every hit.
2. For each hit that is NOT inside task 01's canonical recipe section (or
   already a citation of it), reword it to cite the canonical section by
   name (e.g. "see reference.md's canonical plugin-path resolution recipe
   (Worker prompt section)") rather than restating its own vague
   resolution language.
3. Confirm no hit remains that independently describes an "otherwise the
   plugin cache path found at dispatch"-style resolution without citing
   the canonical recipe.

## Acceptance

- [ ] `grep -rn "resolved at dispatch\|plugin cache path" .claude/skills/*/SKILL.md .claude/skills/*/reference.md`
      — read every hit after the fix: each is either inside the canonical
      recipe section itself, or is a citation of it. Depth ceiling: a
      grep-and-manually-classify check is the correctness-checkable floor
      for a sweep whose exact hit count can't be pinned before breakdown
      names every location; task 01's script test is the behavioral
      complement for the primary evidenced call site.
