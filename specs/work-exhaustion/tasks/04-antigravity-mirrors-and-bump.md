# Task 04: Antigravity mirrors + plugin bump + full-spec sweep

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Priority values run P0 (highest) through P3; the header is optional — absent means P2. -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers, in every task file — and ## Progress / ## Deferred questions are drain-written sections (single writer, main checkout): workers report that content, never write it. -->

Status: in-progress
Depends on: 01, 02, 03
Priority: P2
Budget: 14 turns
Spec: ../SPEC.md (requirement R7)
Touch: antigravity/.agents/workflows/drain.md, antigravity/.agents/workflows/build.md, antigravity/.agents/workflows/autopilot.md, .claude-plugin/plugin.json

## Goal

The Antigravity workflow ports of drain, build, and autopilot carry the
equivalent exhaustion contract (adapted to Antigravity's shape — these
are paraphrased ports, not byte mirrors: docs/memory/
workboard-mirror-verbatim.md), and `.claude-plugin/plugin.json`'s version
is bumped once. Then the whole spec's acceptance list is re-run as a
closing sweep.

## Touch

Only the four files in the header. The `.claude/` skills and
docs/human-gates.md are already landed by tasks 01–03 — read them as the
source to port, never edit them.

## Steps

1. Read the landed diffs of tasks 01–03 (`git log --oneline -12` and the
   three source files) plus `../SPEC.md` R7.
2. Port the contract into the three workflow files: exhaustion loop +
   critique intake + checklist into drain.md; reversible defaults +
   `## Decisions` into build.md (Antigravity has no Skill tool — adapt
   the intake step to its workflow shape, as the existing ports do);
   checklist into autopilot.md.
3. Bump `.claude-plugin/plugin.json`'s version one patch level FROM THE
   VALUE AT THIS TASK'S OWN BASE COMMIT (a sibling may have bumped it
   already — never hard-code the pre-task literal).
4. Closing sweep: run every checkbox in `../SPEC.md`'s Acceptance
   criteria that is automatable; cite each result.

## Acceptance

- [ ] `grep -qi "critique intake" antigravity/.agents/workflows/drain.md` → match (content-coverage, not byte-diff)
- [ ] `grep -qi "reversible default" antigravity/.agents/workflows/drain.md || grep -qi "reversible default" antigravity/.agents/workflows/build.md` → match
- [ ] `grep -qi "checklist" antigravity/.agents/workflows/autopilot.md` → match
- [ ] `python3 -c "import json;print(json.load(open('.claude-plugin/plugin.json'))['version'])"` differs from `git show <this task's base commit>:.claude-plugin/plugin.json | python3 -c "import json,sys;print(json.load(sys.stdin)['version'])"` → true (cite both values)
- [ ] Every automatable checkbox in `../SPEC.md` Acceptance criteria → pass, cited individually in evidence
