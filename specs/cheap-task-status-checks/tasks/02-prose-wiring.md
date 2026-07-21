# Task 02: Point ad hoc status/dependency checks at the cheap tools

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch, Rigor) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Priority values run P0 (highest) through P3; the header is optional — absent means P2. -->
<!-- Status vocabulary: pending → in-progress → done; also blocked (always with an Unblock: line), deferred, skipped, draft (stub awaiting promotion), and needs-verification (implementation complete, acceptance unverified — the verifier flips it to done; scanners treat it as open agent-bounded work, never a needs-attention flag). -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers, in every task file — and ## Progress / ## Deferred questions are drain-written sections (single writer, main checkout): workers report that content, never write it. -->

Status: done
Depends on: none
Priority: P1
Budget: 15 turns
Spec: ../SPEC.md (requirements R1, R2, R3)
Touch: .claude/skills/build/SKILL.md, .claude/skills/drain/SKILL.md, .claude/rules/token-discipline.md

## Goal

Three prose edits, each closing one concretely-located gap where a
header-only check would otherwise default to a full `Read`: `build`'s
closing-step sibling scan now names a `grep` command; `drain/SKILL.md`
gains a short doctrine pointer near step 1 generalizing the
already-existing header-only-check convention beyond that one call site;
`token-discipline.md` gains the same carve-out as the repo-wide doctrine
home both skills can point to.

## Touch

Exactly these three files. Do not touch `drain_frontier.py`,
`reference.md`, or any mirror/plugin-manifest file — those are task 01's
and the closing task's scope.

## Steps

1. In `.claude/skills/build/SKILL.md`, find the closing-step sibling scan
   (the check for whether a sibling `tasks/*.md` in the same directory has
   a `Status: pending` header, used to decide whether to print a `/drain`
   nudge). Reword it to specify `grep -l '^Status: pending'
   specs/<slug>/tasks/*.md` as the check, not a `Read` of each sibling
   file.
2. In `.claude/skills/drain/SKILL.md`, near step 1 (the
   `drain_frontier.py` invocation), add one short doctrine line: any
   header-only check of a task's fields — present anywhere in this
   procedure or added later — uses `grep '^Status:'` / `grep '^Depends
on:'` / `specs/status.sh` / `drain_frontier.py`'s own JSON, never an
   unbounded `Read`.
3. In `.claude/rules/token-discipline.md`'s "Delegation defaults" section,
   add one line stating the same carve-out (grep/`status.sh`/
   `drain_frontier.py`, never a full `Read`, for checking a task's header
   fields alone) — phrased so `.claude/skills/drain/SKILL.md`'s new line
   can point to it as the doctrine home, the same way the section already
   frames its "look around" reads guidance.
4. Verify each of the three phrases below was absent before this edit
   (confirmed absent at spec-authoring time, 2026-07-21) and is present
   after.

## Acceptance

- [x] `grep -n "grep -l.*Status" .claude/skills/build/SKILL.md` returns a
      match at the closing-step sibling-scan location.
      → passed: match at line 270 (closing-step sibling scan), see output above.
      Depth ceiling: this is a prose-only doctrine edit with no runtime to
      exercise — L0 text-presence is the ceiling; the behavioral
      complement is `/build`'s own closing step actually running the
      documented `grep` command on a live repo, which only an attended
      `/build` run can exercise (not unattended-verifiable).
- [x] `grep -n "status.sh" .claude/skills/drain/SKILL.md` returns a match
      near step 1 (anchored on `status.sh` alone — confirmed absent today;
      → passed: match at line 85, in the doctrine line added right after the
      step-1 `drain_frontier.py` invocation, see output above.
      `drain_frontier` already appears pre-existing 3× in this file at
      the step-1 invocation and is not a safe anchor, since it would match
      before this task does any work).
      Depth ceiling: same as above — L0 is the ceiling for a doctrine
      pointer; the behavioral complement is a live drain run actually
      following the pointer, not unattended-verifiable.
- [x] `grep -c "header-only\|never a full .Read." .claude/rules/token-discipline.md`
      → 1 or more.
      → passed: grep -c returned 2, see output above.
      Depth ceiling: same as above.
