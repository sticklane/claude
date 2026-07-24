---
name: handoff
description: Parks session state in bd — a timestamped comment on every touched issue plus one `handoff`-labeled tracking issue carrying the cross-cutting narrative — then tells the user to /clear. Use when a session has grown long or degraded, when switching tasks mid-flight, or when the user says "pick this up later" or "hand this off".
---

Long sessions accumulate dead context that is re-billed every turn and
degrades attention. A clean session resumed from well-parked state
outperforms a long session with accumulated corrections.

Parked state lives in bd, never in a side file: a timestamped comment on
every issue this session still touches, plus one lightweight
`handoff`-labeled issue holding the narrative that belongs to no single
issue. That label is the signal a fresh session looks for — `/resume-handoff`
and the handoff-resume SessionStart hook both query it.

**Autonomous refresh-over-carry path.** When a long-lived autonomous session
refreshes under the session-refresh hook's directive (the wake budget in
`.claude/rules/token-discipline.md`, "Session refresh"), it takes the same
steps below — park the state in bd, then surface the resume pointer where
the restart will actually look for it: the next loop firing, a scheduled
fresh session, or the attended parent — and then **ends its turn**. It does
NOT spawn a detached continuation to carry itself forward: the awaited-
children / no-detachment policy in `.claude/rules/token-discipline.md`
("Awaited children, never detached") governs, so refreshing means handing off
to a fresh context, never seeding this session's own successor.

1. **Check bd is usable first.** Run `bd list --json`. If it fails — no `bd`
   on `PATH`, no `.beads/` in this repo, a non-zero exit — tell the user
   plainly that this skill requires bd here and point them at `agentic init`
   (or `bd init --non-interactive --remote "" --skip-agents`) to set it up,
   then STOP. Do not write a file, do not invent any other fallback, and do
   not run `agentic init` on the user's behalf. This skill is
   plugin-distributed, so an unconfigured repo is a real state to land in,
   not a hypothetical.
2. **Verify completed work before parking.** Run the `verifier` agent on any
   work COMPLETED this session (a task whose Status flipped to done, a spec
   whose criteria you're claiming met) — completed work leaves the session
   verified, not self-reported. The verdict is recorded on the handoff
   issue's `--notes` in step 4. A FAIL flips the task back to
   `Status: in-progress` and becomes the parked next step. If the verifier
   genuinely cannot run before parking, flip the task to
   `Status: needs-verification` instead of leaving an unverified `done` —
   the scanners treat it as open agent-bounded work and the verifier flips
   it to `done` later. Skip only when the session completed nothing (pure
   exploration, or all work is still in flight).
3. **Comment the session state onto every touched issue.** For each bd issue
   this session leaves open or touched:

   ```bash
   bd comment <touched-id> "<ISO date> /handoff — done: <what landed, with evidence>; in flight: <what's partial>; next: <the exact next action for THIS issue>"
   ```

   File anything that has no issue yet before commenting on it — each open
   question, pending decision, or unfinished item this parking records
   becomes its own issue, with a `discovered-from` link where a current
   issue exists (CLAUDE.md's Beads section owns those commands — cite it,
   don't restate it). `bd ready` is where the next session discovers the
   work; state that lives only in prose is how parked work goes invisible to
   the queue.
4. **Create exactly one handoff issue** carrying the cross-cutting narrative
   — the part that belongs to no single issue:

   ```bash
   bd create "Session handoff: <topic>" --labels handoff --type=task \
     --design "<decisions taken this session, each with why and how to reverse; gotchas learned the hard way — wrong assumptions, commands needing flags, slow or flaky tests>" \
     --notes "<status; the exact immediate next action; what to resume with (a skill or command); what's blocking, or nothing; files touched, one line each; the step-2 verifier verdict and which acceptance criteria pass right now>"
   ```

   Decisions are what a compressed summary silently loses, and a resumer who
   can't see them re-makes them differently (docs/external-playbooks.md,
   "Handoffs", the Cognition bullet) — so `--design` is not optional padding.
   Point `--notes` at full artifacts (the task file, `evidence/` paths,
   commits) rather than re-summarizing them: facts and paths only, no
   conversation history.
5. **Link the handoff issue to every issue it parks** — the edges
   `/resume-handoff` walks to rebuild context:

   ```bash
   bd dep add <handoff-id> <touched-id> -t tracks
   ```
6. Commit work-in-progress to the working branch if the tree is dirty —
   parked state pointing at an uncommitted tree is fragile.
7. Run /distill first if there were corrections worth keeping — handoff
   preserves state, distill preserves lessons; they're different.
8. Tell the user: `/clear`, then resume with `/resume-handoff`, naming the
   handoff issue's id. Never instruct an ad hoc "read the issue and
   continue": that bypasses the tracker reconciliation and consumption steps
   the resume skill exists to guarantee (its own doctrine, and the
   handoff-resume hook says the same). Close with:
   `Next stage: none — /clear, then /resume-handoff picks the work up`.
