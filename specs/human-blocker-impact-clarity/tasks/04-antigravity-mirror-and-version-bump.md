# Task 04: Mirror the derivation into antigravity + bump plugin.json

Status: done
Depends on: 02
Priority: P2
Budget: 16 turns
Spec: ../SPEC.md (requirements R7, R8)
Touch: antigravity/.agents/workflows/drain.md, .claude-plugin/plugin.json

## Goal

`antigravity/.agents/workflows/drain.md`'s mirrored "HUMAN.md filing (R2)"
section (~line 1162) carries the same `Blocks:` derivation guidance task 02
added to the `.claude/` source, scoped to the five checklist-source rows
that file's text already enumerates. `.claude-plugin/plugin.json`'s
`"version"` is bumped, since this spec changes `/drain`'s behavior in both
the `.claude/` source and its `antigravity/` mirror.

## Touch

Only `antigravity/.agents/workflows/drain.md` and
`.claude-plugin/plugin.json`. Do not touch `.claude/skills/drain/reference.md`
(already landed by task 02 — read it, don't edit it), `.claude/rules/human-blockers.md`,
or `HUMAN.md`.

## Steps

1. Read task 02's landed changes to `.claude/skills/drain/reference.md`'s
   "HUMAN.md filing (R2)" section (this task depends on 02).
2. In `antigravity/.agents/workflows/drain.md`'s mirrored "HUMAN.md filing
   (R2)" section (~line 1162-1178), add the same `Blocks:` derivation
   guidance, scoped to the five rows that file's text already enumerates:
   the mechanical `Depends on:`/"unblocking-power" derivation citation for
   its three `ask`/`run` rows ("deferred questions still unanswered",
   "`Unblock: ask:` blocked tasks", "`Unblock: run:` blocked tasks"), and
   the same two literal fixed phrases from task 02 for its two `decide`
   rows ("decision-shaped or gate-refused stubs", "NOT-READY specs").
   Do NOT add a `Contradicts-premise`-deferred row — that row is a
   pre-existing gap in this mirror, out of scope for this spec (see
   SPEC.md's Out of scope section).
3. Before editing `.claude-plugin/plugin.json`, capture its current
   `"version"` value (e.g. `git show $(git merge-base main HEAD):.claude-plugin/plugin.json`
   piped through `grep version`, or simply read the file). Bump the
   version (increment the patch component) so the file's `"version"` value
   differs from its pre-task value.

## Acceptance

- [x] `grep -c 'promotion of this stub to a dispatchable task' antigravity/.agents/workflows/drain.md` → 1
      (phrase absent today, count 0, verified 2026-07-19)
      Evidence: drain re-ran the command post-merge → `1`. PASS.
- [x] `grep -c 'breakdown of this spec into dispatchable tasks' antigravity/.agents/workflows/drain.md` → 1
      (phrase absent today, count 0, verified 2026-07-19)
      Evidence: drain re-ran the command post-merge → `1`. PASS.
- [x] `sed -n '/\*\*HUMAN.md filing (R2)\.\*\*/,/^## /p' antigravity/.agents/workflows/drain.md | grep -c 'unblocking-power'` → ≥ 1
      (section-scoped — this file already contains `unblocking-power`
      elsewhere, in its mirrored step-2 tie-break text, so an unscoped grep
      would pass vacuously; this confirms the derivation citation actually
      landed in the HUMAN.md-filing section, not merely present elsewhere.
      Section marker exists at drain.md:1162 and the section-scoped count
      is 0 today, verified 2026-07-19)
      Evidence: drain re-ran the command post-merge → `1`. PASS.
- Depth ceiling (covers the three mirror checks above): L0/L1 on a
  mirrored prose port — behavioral complement is the closure-triggered
  cross-reference sweep of `.claude/rules/mirror-verification.md` plus a
  procedural-equivalence read of the ported derivation against task 02's
  source per `.claude/rules/mirror-procedure-discipline.md` (an agent or
  human read, recorded in the task evidence).
- [x] `grep -c '"version"' .claude-plugin/plugin.json` → 1 (still exactly
      one version field), AND its value differs from the value at this
      task's own base commit: `git show $(git merge-base main HEAD):.claude-plugin/plugin.json | grep '"version"'`
      compared against the current file's `"version"` line — they must not
      match. Do not hard-code a specific from/to version string; compare
      against your own branch's base commit so a sibling task's concurrent
      bump never false-fails this check.
      Evidence: drain re-ran post-merge → base commit 30bdd78 had
      `"version": "0.9.23"`, current file has `"version": "0.9.24"`. PASS.

Worker note (recorded by drain, not the worker): the implementation worker
left this task file's Status/checkboxes unedited, citing the file as
outside its Touch: scope. That reads the Touch header too narrowly — the
task file's own queue-state fields are always in scope for a worker's
close-out, per every sibling task in this spec. Drain applied the
close-out edits itself post-merge after independently re-verifying all
four acceptance commands above.
