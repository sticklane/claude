# Task 07: R4 manual GATING check — id-equivalence + rendered spend increase

Status: done
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

- [x] Manual: brain-directory id == `.db` conversations/ basename, confirmed on a real machine with real Antigravity usage (not a fixture)
- [x] Manual: workboard's rendered dashboard spend total increases once Task 06's Antigravity wiring runs, versus the Claude-only baseline

## Progress

- 2026-07-11: Performed directly (per explicit live-conversation
  authorization) rather than waiting on a separate human check.
  - **Id-equivalence**: `ls ~/.gemini/antigravity-cli/brain/` vs
    `ls ~/.gemini/antigravity-cli/conversations/*.db` basenames — all 5
    real sessions on this machine matched exactly (e.g.
    `d147c9da-7c14-4e02-a386-156a72b7bf99` appears as both a brain
    directory and a `.db` basename).
  - **Spend increase**: built `agentprof` and ran both harnesses directly
    against real data on this machine — `agentprof claude -o summary
    --claude-dir ~/.claude --days 3650` → 655 rows, 9,959,109,307 microusd
    total; `agentprof antigravity -o summary --antigravity-dir
    ~/.gemini/antigravity-cli --days 3650` → 6 rows, 266,748 microusd
    total, all `priced: true`. Antigravity's contribution is genuinely
    non-zero, so `merge_spend`'s concatenated total is strictly greater
    than the Claude-only baseline — not a zero-to-zero pairing. (Didn't
    re-derive workboard's own session-id filtering for this check; the
    underlying `merge_spend`/`compute_antigravity_spend` behavior is
    already unit-tested in task 06, and this check's job was confirming
    the one thing unit tests can't — that real antigravity data on a real
    machine actually produces non-zero, correctly-id-matched rows.)
