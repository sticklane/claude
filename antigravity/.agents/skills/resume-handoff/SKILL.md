---
name: resume-handoff
description: Deterministically resumes work from a HANDOFF.md left by the handoff skill or a session-refresh — locates it, reads it in full, resumes the recorded next step, then deletes the consumed file. Use when the user says "resume", "resume handoff", "continue from the handoff", or "pick up where we left off".
---

A `HANDOFF.md` only helps if the next conversation actually reads and acts
on it. Freeform "read it and continue" prose is advisory, not a binding
instruction — when the live user message asks for something else, that
something else correctly wins, and the handoff goes un-acted-on. This
skill is the deterministic alternative: invoke it by name to guarantee the
resume actually happens, instead of hoping ad hoc compliance is
consistent.

1. **Locate.** Find every file literally named `HANDOFF.md` under the
   project root, skipping `.git`, worktree copies, `node_modules`,
   `fixtures`, and `test_fixtures` directories.
   - Zero found: tell the user there's nothing to resume and stop.
     `Next stage: none — no handoff found`.
   - Multiple found: list the paths and ask the user which one (or infer
     from the live request if it already names the task) — never guess
     silently.
2. **Read** the chosen file in full before doing anything else. Do not
   re-derive state it already captures.
3. **Surface, then resume.** State the resumed task and its recorded
   immediate next step in 1-2 sentences, then continue directly into that
   next step — UNLESS the recorded next step is itself one of the gated
   execution stages (build/drain/prioritize). A handoff file is
   not a live user authorization for those (docs/human-gates.md, cited not
   restated) — name the recommended stage and get the user's explicit
   go-ahead before invoking it.
4. **Consume.** Once the handoff's content is captured and the resumed
   work is underway, remove the consumed `HANDOFF.md` and commit the
   deletion on its own (`chore: consume handoff, resume <short task>`) —
   this is what stops a repeat conversation from being pointed at stale
   state. If the tree can't take a clean commit right now (mid-merge,
   unrelated dirty files), leave the file in place and tell the user
   cleanup is deferred.

`Next stage: none — the resumed task's own next stage governs from here`.
