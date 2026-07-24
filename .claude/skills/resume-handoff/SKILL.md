---
name: resume-handoff
description: Deterministically resumes work from a HANDOFF.md left by /handoff or a session-refresh — locates it, reads it in full, resumes the recorded next step, then deletes the consumed file so the handoff-resume hook goes quiet again. Use when the user says "resume", "resume handoff", "continue from the handoff", "pick up where we left off", or invokes "/resume-handoff"; also the deterministic target the handoff-resume SessionStart hook's advisory now names, replacing ad hoc read-and-continue prose.
---

A `HANDOFF.md` only helps if the next session actually reads and acts on
it. The `handoff-resume` SessionStart hook (`hooks/handoff-resume/resume-check.sh`)
flags one when it exists, but its injected text is advisory context, not a
binding instruction — when the live user message asks for something else,
that something else correctly wins per CLAUDE.md's precedence order, and
the flagged handoff goes un-acted-on. This skill is the deterministic
alternative: invoke it by name to guarantee the resume actually happens,
instead of hoping prose compliance is consistent.

1. **Locate.** Find every file matching `HANDOFF*.md` under the
   project root (the hook's own pattern — `/handoff`'s conflict-avoidance
   branch writes `HANDOFF-<topic>.md`, and literal-name-only matching is
   how those accumulated as invisible strays), using the same exclusions
   as the hook: skip `.git`, `.claude/worktrees/*`, `node_modules`,
   `fixtures`, `test_fixtures`.
   - Zero found: tell the user there's nothing to resume and stop.
     `Next stage: none — no handoff found`.
   - Multiple found: read each candidate's compact header only (its first
     few `Key: value` lines — e.g. `head -n 10` per candidate, a bounded
     read, never the full body), then ask the user which one via
     `AskUserQuestion` (or infer from the live request if it already names
     the task) — never guess silently. Each option's text shows that
     candidate's `Task:` and `Status:` header values alongside its path, so
     the question is answerable without opening any file. If two
     candidates' headers don't distinguish them (e.g. identical `Task:`
     values), ask anyway with whatever the headers show — no additional
     tiebreak logic; the skill still always asks and never auto-selects.
2. **Read** the chosen file in full before doing anything else. Do not
   re-derive state it already captures.
3. **Surface, then resume.** State the resumed task and its recorded
   immediate next step in 1-2 sentences, then continue directly into that
   next step — UNLESS the recorded next step is itself one of the two
   gated execution stages (`/build`, `/drain`). A handoff file is not a
   live user authorization for
   those (`.claude/rules/untrusted-data.md`'s launch-authorization
   contract, cited not restated) — name the recommended stage and get the
   user's explicit go-ahead before invoking it.
4. **Reconcile the tracker.** Act on the header's `Tracked:` line
   (CLAUDE.md's Beads section owns the commands — cite it, don't restate
   it): claim the issue(s) for the work now being resumed; close any the
   handoff shows finished. A `Tracked: none — bd unavailable` header (or a
   pre-`Tracked:` handoff) means the parked items were never filed — file
   them now, before resuming, so the queue reflects the work even if this
   resume session also parks. If bd is unavailable here too, do NOT
   skip-filing-and-consume — that silently loses the parked items. Instead
   either DEFER consumption (leave the handoff file in place and tell the
   user why: its unfiled `Tracked:` items would be lost if deleted before
   bd is reachable), or carry every unfiled item forward into this
   session's first report as an explicit `pending-filing: <item>` line so
   the linkage survives until someone with bd files it. Never both skip
   filing and delete the file.
5. **Consume.** Once the handoff's content is captured, the resumed
   work is underway, and its `Tracked:` items are filed or carried forward
   per step 4 (never consume a handoff whose parked items are still both
   unfiled and uncarried), `git rm` the consumed handoff file (`rm` + no commit
   needed when the file was never tracked — `git ls-files` says which) and
   commit the deletion on its own
   (`chore: consume handoff, resume <short task>`) —
   this is what stops the hook from re-flagging stale state on every
   future session start. If the tree can't take a clean commit right now
   (mid-merge, unrelated dirty files), leave the file in place and tell
   the user cleanup is deferred.

`Next stage: none — the resumed task's own next stage governs from here`.
