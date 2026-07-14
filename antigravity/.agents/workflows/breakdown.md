---
description: Split a SPEC.md into one-conversation task files with dependencies and a parallelization map
---

Use the breakdown skill (.agents/skills/breakdown/SKILL.md) and follow it exactly, applying it to whatever arguments follow the command. If no arguments were given and the skill needs a target, ask for it.

## The `Unblock:` line (blocked and waiting items)

An item that stops carries its own move as a machine-readable `Unblock:` line,
on the line immediately after `Status:`, in one of three narrowest-fit forms:
`Unblock: run: <shell command>` (a command checks or clears it — display and
agent-run only, never raw exec), `Unblock: agent: <prompt>` (a headless agent
run can clear it), or `Unblock: ask: <exact question>` (a human must answer).
A task file takes an `Unblock:` line ONLY with `Status: blocked` and never
uses `waiting` — drain writes it when recording a BLOCKED flip, and an
attended /build writes it in the same edit as the blocked status; a
`SPEC.md` may carry the header pair `Status: waiting` + `Unblock:` as its
only spec-level status, and a successful recheck removes that pair (specs
have no `pending` to flip to).

**Cross-spec file collision → `Status: blocked` + `Unblock: run:`, not
`pending`.** When a spec's own text names a sibling spec it must land
after (both edit the same file), check whether the collision is broader
than stated — a spec touching a skill mirrored across `.claude`/
`antigravity`/`codex` legs likely collides on all of them, not just the
one file a Sequencing note happens to name. Encode the real collision by
marking every affected task `Status: blocked` with `Unblock: run: for f in
specs/<sibling>/tasks/*.md; do grep -q '^Status: done' "$f" || echo "not
done: $f"; done` rather than `pending` — the only mechanical way to stop
an unattended drain from landing both specs concurrently. Nothing
auto-flips this: drain does not re-run `Unblock: run:` on a pre-existing
blocked task, so a human or later session must re-check and flip the
status once the sibling spec's tasks are all `done`.
