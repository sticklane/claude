---
name: clone-audit
description: Produces a clone/duplicate-code report for a mixed TS/Go repo using jscpd, a read-only audit that never auto-fixes — findings go to a normal task/spec, never an in-place edit. Use when the user says "find duplicate code", "clone detection", "run a clone audit", "check for copy-pasted code", or "duplicate code report".
argument-hint: "[repo path to audit, defaults to cwd]"
---

**Read-only contract.** clone-audit makes NO edits. It runs a clone
detector, reports what it finds, and stops — every finding's next step is a
normal task/spec filed through the pipeline, never an in-audit rewrite. This
is the same read-only shape harness-audit uses for its five checklist areas
(`.agents/skills/harness-audit/SKILL.md`), applied to one narrower question:
where does this repo have duplicated code.

**Why a separate skill, not `ctx dupes` or a harness-audit area.** `ctx`
stays model-free and per-file (structure queries only); clone detection is
whole-repo cross-file comparison and belongs to a different tool shape.
harness-audit's checklist areas are periodic hygiene checks over a fixed
list — clone detection is a report a human requests on demand, not a
recurring area. `specs/ctx-static-analysis-augmentation/SPEC.md` (F2) records
this choice.

## Procedure

1. Confirm the target repo at `$ARGUMENTS` (default: cwd) mixes TS and Go, or
   run only the relevant stack's recipe if it's single-stack.
2. Run the documented recipe for each stack present — see
   [reference.md](reference.md) for the exact commands, one worked example
   per stack, and the non-normative fooszone three-homography case. Both
   recipes route through `jscpd`, which supports `typescript` and `go` as
   format targets — a repo does not need two separate detectors.
3. If the recipe's network install (`npx jscpd`) is unavailable in this
   environment, say so explicitly ("clone-audit: jscpd unreachable, no
   network install access") rather than silently skipping — the same
   explicit-skip discipline harness-audit's checklist areas use.
4. Report findings as a ranked list — file + line range + duplicated-token
   count per clone, largest first — and stop. Do not refactor, rename, or
   merge duplicated code as part of this skill; that is normal follow-up
   work through the pipeline.

## Dispatch tier

Running the detector and parsing its report is mechanical — dispatch it as
a scout-tier conversation (read-only; the scout skill, on the scout tier of
the active runtime profile in `runtimes/`) per
`.claude/rules/token-discipline.md`'s "Dispatch authoring" section (cited,
not restated); only the final ranking pass needs judgment and runs on the
session model.

Next stage: none — file findings as tasks/specs per normal pipeline.
