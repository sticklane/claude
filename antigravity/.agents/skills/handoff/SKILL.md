---
name: handoff
description: Writes a self-contained handoff file for resuming work in a fresh conversation. Use when a conversation has grown long or degraded, when switching tasks mid-flight, or when the user says "pick this up later" or "hand this off".
---

Long conversations accumulate dead context that degrades attention. A clean
conversation resumed from a good handoff file outperforms a long one with
accumulated corrections.

**Autonomous refresh-over-carry path.** A long-lived autonomous run that
refreshes under its session-refresh directive follows the same steps below —
write the handoff file, then surface the resume pointer where the restart
will look: the next loop firing, a scheduled fresh conversation, or the
attended parent — then ends its turn. It must NOT spawn a detached
continuation of itself: the "Awaited children, never detached" policy in
`AGENTS.md` governs, so refreshing hands work to a fresh context rather than
seeding this run's own successor.

1. Write `HANDOFF.md` next to the active task/spec file (or at the repo
   root if there isn't one). **Check first whether that default path is
   already occupied by an unrelated task's handoff** (another concurrent
   run's own in-flight parking file — read it far enough to tell if its Task
   section describes different work than yours); if so, do not overwrite it
   — pick a distinctly-named file instead (e.g. `HANDOFF-<short-topic>.md`)
   and name that path explicitly in your final message, since the default
   single-path convention assumes only one handoff is ever parked at a time.
   **The file opens with a fixed compact header block** — these five
   `Key: value` lines are the first lines of every `HANDOFF.md`, ahead of
   the free-form prose sections below (which are unchanged):
   - `Task:` — a one-line name for the work (the spec/task path or a short
     description). Required: this is the field a resumer actually compares
     between candidates, since `Status:`/`Blocking on:` are often identical
     across two in-flight threads.
   - `Status:` — the task's current status (e.g. `in-progress`).
   - `Next step:` — the exact immediate next action.
   - `Resume with:` — the skill or command to run to continue.
   - `Blocking on:` — what's blocking, or `nothing`.

   So every `HANDOFF.md` opens with these five lines, verbatim shape:

```
Task: <spec/task path or one-line description of the work>
Status: <in-progress | needs-verification | blocked | ...>
Next step: <the exact immediate next action>
Resume with: <the skill or command to run, e.g. /build or /resume-handoff>
Blocking on: <what's blocking, or nothing>
```

   After that header block, contain only what a fresh agent needs:
   - **Task**: what we're doing and the task/spec file path.
   - **State**: what's done (with evidence), what's in flight, exact next step.
   - **Files touched**: paths, one line each on what changed and why.
   - **Gotchas**: everything learned the hard way this session — wrong
     assumptions, commands that need flags, tests that are slow/flaky.
   - **Verification**: which acceptance criteria pass right now, which don't.
     Facts and paths only — no narrative. Over a page means dead weight.
2. Apply the verifier skill to any work COMPLETED this conversation (a
   task whose Status flipped to done, a spec whose criteria you're
   claiming met) before parking — completed work leaves the conversation
   verified, not self-reported. Record the verdict in the handoff's
   Verification section; a FAIL flips the task back to
   `Status: in-progress` and becomes the handoff's exact next step. If
   the verifier genuinely cannot run before parking, flip the task to
   `Status: needs-verification` instead of leaving an unverified `done` —
   the scanners treat it as open agent-bounded work and the verifier
   flips it to `done` later. Skip only when the conversation completed
   nothing (pure exploration, or all work is still in flight).
3. Commit work-in-progress to the working branch if the tree is dirty (a
   handoff pointing at an uncommitted tree is fragile).
4. Apply the distill skill first if there were corrections worth keeping —
   handoff preserves state, distill preserves lessons; they're different.
5. Tell the user: start a new conversation with
   "Read <path>/HANDOFF.md and continue."

`Next stage: none — start a new conversation and resume from the handoff file`.
