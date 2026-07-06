# Task 05: Ship gates — antigravity mirrors and plugin version bump

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Priority values run P0 (highest) through P3; the header is optional — absent means P2. -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers, in every task file — and ## Progress / ## Deferred questions are drain-written sections (single writer, main checkout): workers report that content, never write it. -->

Status: done
Depends on: 01, 02
Priority: P1
Budget: 12 turns
Spec: ../SPEC.md (requirement R7)
Touch: antigravity/.agents/workflows/drain.md, antigravity/.agents/skills/breakdown/SKILL.md, .claude-plugin/plugin.json

## Goal

The antigravity mirrors reflect the rolling-window scheduler landed by
task 01 and the `Group:` grammar landed by task 02; `plugin.json`'s
version is bumped; and the toolkit's two standing ship gates
(`evals/lint-ultra-gate.sh`, `claude plugin validate .`) both pass. This
is the closing task CLAUDE.md's authoring conventions require whenever a
spec's tasks change `.claude/skills/` files — it centralizes the mirror
+ version-bump obligation in one Touch list instead of leaving it
implicit in tasks 01/02 (workboard-cli's closing task 04 is the cited
model).

## Touch

In scope: exactly the three listed paths. `antigravity/.agents/
workflows/drain.md` is drain's human-only mirror (its body IS the
workflow) — update its scheduling description to match task 01's
rewrite. `antigravity/.agents/skills/breakdown/SKILL.md` is breakdown's
model-invocable mirror — its 5-line workflow pointer needs no edit, but
the skill body must gain content-coverage for the `Group:` grammar task
02 added.

Out of scope: anything under `.claude/`, `tests/`, `docs/`, or `evals/`
other than reading `evals/lint-ultra-gate.sh` to run it (don't edit it).
Per docs/memory/workboard-mirror-verbatim.md: these are paraphrased
ports, not byte-identical mirrors — write for content coverage of the
concepts/identifiers, never chase a `diff → no output` result.

## Steps

1. Confirm tasks 01 and 02 are `Status: done` before starting (this
   task's Touch is only correct once both source files are final).
2. Read the current `antigravity/.agents/workflows/drain.md` sections
   covering dispatch/group-mode and rewrite them to carry the
   rolling-window semantics (window admission, top-up on verdict, serial
   merge + rebase recovery, R8/R8a/R9 termination properties) at the
   same level of paraphrase the rest of the file already uses — do not
   attempt a byte-identical port of SKILL.md's new prose.
3. Read the current `antigravity/.agents/skills/breakdown/SKILL.md` and
   add content-coverage for the `Group:` grammar (the concept and the
   `- Group: NN, NN` example), matching task 02's SKILL.md change.
4. Bump the `version` field in `.claude-plugin/plugin.json` (patch bump
   is sufficient — this is a skill-behavior change, not a schema change).
5. Run `bash evals/lint-ultra-gate.sh` and `claude plugin validate .`;
   fix anything either flags before marking this task done.

## Acceptance

- [x] `claude plugin validate .` → pass
      → "✔ Validation passed", exit 0 (verifier PASS; evidence/05-ship-gates-and-mirrors.md)
- [x] `bash evals/lint-ultra-gate.sh` → exit 0
      → "lint-ultra-gate: OK — all ultra mentions gated in 4 files", exit 0
- [x] plugin.json version changed from its pre-task value: `git log -1
      --format=%H -- .claude-plugin/plugin.json` before/after differ, or
      simply confirm the checked-in `version` string is not `0.8.14`
      → 0.8.15 → 0.8.16 (not 0.8.14; changed from base 819c77c)
- [x] `grep -ci 'rolling.window\|parallel-window' antigravity/.agents/workflows/drain.md`
      → ≥ 1
      → 5
- [x] `grep -ci 'group:' antigravity/.agents/skills/breakdown/SKILL.md`
      → ≥ 1
      → 6

## Discovered

- `antigravity/.agents/skills/breakdown/SKILL.md`'s "Hand off" section still says "its group throughput mode hands you concurrent Agent Manager launches" — stale after this task renamed that mode to the rolling window in drain.md. See specs/drain-rolling-window/tasks/09-fix-stale-group-mode-antigravity-handoff.md.
- Task 05's own acceptance criterion hard-coded the pre-task plugin.json version as `0.8.14`, but main had already advanced to `0.8.15` from a sibling task's bump by the time this task ran — a version-bump criterion pinning an exact pre-value can go stale when sibling tasks bump the same file first. See specs/drain-rolling-window/tasks/10-version-bump-criteria-use-relative-check.md.
