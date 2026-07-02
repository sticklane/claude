---
name: handoff
description: Writes a self-contained handoff file for resuming work in a fresh conversation. Use when a conversation has grown long or degraded, when switching tasks mid-flight, or when the user says "pick this up later" or "hand this off".
---

Long conversations accumulate dead context that degrades attention. A clean
conversation resumed from a good handoff file outperforms a long one with
accumulated corrections.

1. Write `HANDOFF.md` next to the active task/spec file (or at the repo
   root if there isn't one), containing only what a fresh agent needs:
   - **Task**: what we're doing and the task/spec file path.
   - **State**: what's done (with evidence), what's in flight, exact next step.
   - **Files touched**: paths, one line each on what changed and why.
   - **Gotchas**: everything learned the hard way this session — wrong
     assumptions, commands that need flags, tests that are slow/flaky.
   - **Verification**: which acceptance criteria pass right now, which don't.
   Facts and paths only — no narrative. Over a page means dead weight.
2. Commit work-in-progress to the working branch if the tree is dirty (a
   handoff pointing at an uncommitted tree is fragile).
3. Apply the distill skill first if there were corrections worth keeping —
   handoff preserves state, distill preserves lessons; they're different.
4. Tell the user: start a new conversation with
   "Read <path>/HANDOFF.md and continue."
