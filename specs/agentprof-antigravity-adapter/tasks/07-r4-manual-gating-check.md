# Task 07: R4 manual GATING check — id-equivalence + rendered spend increase

Status: blocked
Unblock: ask: With a real Antigravity `.db` present on this machine (`~/.gemini/antigravity-cli/conversations/*.db`), please confirm (1) a `scan_antigravity()` brain-directory id (`~/.gemini/antigravity*/brain/<id>/`) equals that same session's `.db` basename under `conversations/`, and (2) that running the workboard dashboard now shows a higher rendered total spend than the Claude-only baseline before this change. Reply here with the result (pass/fail and what you observed) so this task's Status can be flipped to done.
Depends on: 06
Priority: P2
Budget: 4 turns
Spec: ../SPEC.md (final acceptance criterion, "GATING manual check")
Touch: none — verification only, no code changes

## Goal

The one load-bearing empirical claim R4's whole fix depends on is
confirmed on a real machine: a `scan_antigravity()` brain-directory id
actually equals that session's `.db` basename under `conversations/` (the
identity Task 06's `cascade_ids` filter assumes), and the workboard
dashboard's rendered total spend measurably increases once the Antigravity
call is wired in, versus the Claude-only baseline. This depends on this
machine's mutable `~/.gemini` state, so it cannot run in CI — it is the
one acceptance criterion the spec calls out as "not optional, not
skippable even though it can't run in CI."

## Touch

No files change in this task. It is a verification-only closing step for
R4 — if the check ever fails, the correct next step is a bug-fix task
against Task 06's `compute_antigravity_spend`/`merge_spend`, not an edit
made directly against this task's Touch (which is empty by design).

## Steps

This step cannot be run by an unattended `/drain` worker (it depends on a
human's local, mutable `~/.gemini` state, not a repo file) — mark it
manual-pending per docs/memory/unattended-worker-tool-limits.md rather
than attempting it headless:

1. On a machine with real Antigravity usage, list a brain-directory id
   from `~/.gemini/antigravity*/brain/<id>/` and a `.db` basename from
   `~/.gemini/antigravity-cli/conversations/<cascade_id>.db` for the same
   session, and confirm the two ids are equal.
2. Run the workboard dashboard (or its render path) once before this
   spec's Antigravity wiring is active and once after, and confirm the
   rendered total spend increases (not zero-to-zero) once the Antigravity
   call is wired in.
3. Record the result (pass/fail, and what was observed) in this task's
   `## Progress` when flipping Status.

## Acceptance

- [ ] Manual: brain-directory id == `.db` conversations/ basename, confirmed on a real machine with real Antigravity usage (not a fixture)
- [ ] Manual: workboard's rendered dashboard spend total increases once Task 06's Antigravity wiring runs, versus the Claude-only baseline
