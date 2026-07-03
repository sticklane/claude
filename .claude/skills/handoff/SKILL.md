---
name: handoff
description: Writes a self-contained handoff file for resuming work in a fresh session, then tells the user to /clear. Use when a session has grown long or degraded, when switching tasks mid-flight, or when the user says "pick this up later" or "hand this off".
---

Long sessions accumulate dead context that is re-billed every turn and
degrades attention. A clean session resumed from a good handoff file
outperforms a long session with accumulated corrections.

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
2. Commit work-in-progress to the working branch if the tree is dirty (a
   handoff pointing at an uncommitted tree is fragile).
3. Run /distill first if there were corrections worth keeping — handoff
   preserves state, distill preserves lessons; they're different.
4. Tell the user: `/clear`, then resume with
   "Read <path>/HANDOFF.md and continue." Close with:
   `Next stage: none — /clear and resume from the handoff file`.
