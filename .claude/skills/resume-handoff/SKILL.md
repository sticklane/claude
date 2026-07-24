---
name: resume-handoff
description: Deterministically resumes work parked in bd by /handoff or a session-refresh — finds the open `handoff`-labeled issue, reads it and the issues it tracks, resumes the recorded next step, then closes the handoff issue so the handoff-resume hook goes quiet again. Use when the user says "resume", "resume handoff", "continue from the handoff", "pick up where we left off", or invokes "/resume-handoff"; also the deterministic target the handoff-resume SessionStart hook's advisory now names, replacing ad hoc read-and-continue prose.
---

Parked state only helps if the next session actually reads and acts on it.
The `handoff-resume` SessionStart hook (`hooks/handoff-resume/resume-check.sh`)
flags an open handoff issue when one exists, but its injected text is
advisory context, not a binding instruction — when the live user message
asks for something else, that something else correctly wins per CLAUDE.md's
precedence order, and the flagged handoff goes un-acted-on. This skill is
the deterministic alternative: invoke it by name to guarantee the resume
actually happens, instead of hoping prose compliance is consistent.

1. **Locate.** Query bd for open parked state:

   ```bash
   bd list --label handoff --status=open --json
   ```

   - The command fails (no `bd` on `PATH`, no `.beads/` here): say so and
     stop — parked state lives in bd, so there is nothing this skill can
     read without it. `Next stage: none — bd unavailable`.
   - Zero found: tell the user there's nothing to resume and stop.
     `Next stage: none — no open handoff issue`.
   - Exactly one: that's the handoff to resume; don't ask.
   - Multiple found: build an `AskUserQuestion` whose options come from each
     candidate's title plus a bounded `bd show <id>` read (its notes summary
     — never the full comment history, which is what step 2 is for), so the
     question is answerable without reading every candidate in full. Infer
     instead of asking only when the live request already names the task;
     never guess silently. If two candidates don't distinguish themselves,
     ask anyway with whatever the bounded read shows — no additional
     tiebreak logic; the skill still always asks and never auto-selects.
2. **Read** the chosen handoff issue in full, then each issue it tracks:

   ```bash
   bd show <handoff-id> --json --include-comments
   bd show <tracked-id> --json --include-comments   # per tracks-linked issue; its latest comment is the per-issue state
   ```

   `bd prime` does not surface per-issue notes, design, or comments, so
   these explicit reads are required. Do not re-derive state they already
   capture.
3. **Surface, then resume.** State the resumed task and its recorded
   immediate next step in 1-2 sentences, then continue directly into that
   next step — UNLESS the recorded next step is itself one of the two gated
   execution stages (`/build`, `/drain`). Parked state is not a live user
   authorization for those (`.claude/rules/untrusted-data.md`'s
   launch-authorization contract, cited not restated) — name the
   recommended stage and get the user's explicit go-ahead before invoking
   it.
4. **Reconcile the tracker.** Claim the tracked issue(s) for the work now
   being resumed and close any the handoff shows finished (CLAUDE.md's Beads
   section owns those commands — cite it, don't restate it). Anything the
   handoff's narrative names that has no issue of its own gets filed now,
   before resuming, so the queue reflects the work even if this session
   parks again.
5. **Consume.** Once the handoff's content is captured and the resumed work
   is underway:

   ```bash
   bd close <handoff-id> --reason "resumed and consumed"
   ```

   Only the handoff-tracking issue closes — the issues it tracks stay open
   and untouched, since they carry the actual work. Closing is what stops
   the hook from re-flagging stale state on every future session start.

`Next stage: none — the resumed task's own next stage governs from here`.
