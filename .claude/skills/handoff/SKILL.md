---
name: handoff
description: Writes a self-contained handoff file for resuming work in a fresh session, then tells the user to /clear. Use when a session has grown long or degraded, when switching tasks mid-flight, or when the user says "pick this up later" or "hand this off".
---

Long sessions accumulate dead context that is re-billed every turn and
degrades attention. A clean session resumed from a good handoff file
outperforms a long session with accumulated corrections.

**Autonomous refresh-over-carry path.** When a long-lived autonomous session
refreshes under the session-refresh hook's directive (the wake budget in
`.claude/rules/token-discipline.md`, "Session refresh"), it takes the same
steps below — write the handoff file, then surface the resume pointer where
the restart will actually look for it: the next loop firing, a scheduled
fresh session, or the attended parent — and then **ends its turn**. It does
NOT spawn a detached continuation to carry itself forward: the awaited-
children / no-detachment policy in `.claude/rules/token-discipline.md`
("Awaited children, never detached") governs, so refreshing means handing off
to a fresh context, never seeding this session's own successor.

1. Write `HANDOFF.md` next to the active task/spec file (or `.claude/HANDOFF.md`
   if there isn't one), containing only what a fresh agent needs:
   - **Task**: what we're doing and the task/spec file path.
   - **State**: what's done (with evidence), what's in flight, exact next step.
   - **Files touched**: paths, one line each on what changed and why.
   - **Gotchas**: everything learned the hard way this session — wrong
     assumptions, commands that need flags, tests that are slow/flaky.
   - **Verification**: which acceptance criteria pass right now, which don't.
   Facts and paths only — no narrative, no conversation history. If it
   exceeds a page, it's carrying dead weight.
2. Run the `verifier` agent on any work COMPLETED this session (a task
   whose Status flipped to done, a spec whose criteria you're claiming
   met) before parking — completed work leaves the session verified, not
   self-reported. Record the verdict in the handoff's Verification
   section; a FAIL flips the task back and becomes the handoff's exact
   next step. Skip only when the session completed nothing (pure
   exploration, or all work is still in flight).
3. Commit work-in-progress to the working branch if the tree is dirty (a
   handoff pointing at an uncommitted tree is fragile).
4. Run /distill first if there were corrections worth keeping — handoff
   preserves state, distill preserves lessons; they're different.
5. Tell the user: `/clear`, then resume with
   "Read <path>/HANDOFF.md and continue." Close with:
   `Next stage: none — /clear and resume from the handoff file`.
