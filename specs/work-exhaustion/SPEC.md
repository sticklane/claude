# Work exhaustion: consume the queue until nothing is dispatchable

Status: open
Priority: P1

## Problem

In real usage (maintainer feedback, 2026-07-08) the pipeline stalls
between stages instead of consuming work:

- Sessions stop when a dispatched unit finishes rather than proceeding
  to the next step of the loop (collect the verdict, merge, top up,
  claim the next item).
- Draft specs and discovered-work stubs sit inert until a human manually
  runs /critique and /breakdown — even though /critique is
  model-invocable and drain already auto-invokes /breakdown on
  `Breakdown-ready: true` specs; the missing link is nobody runs the
  critique step unprompted.
- Decisions that have a reversible default interrupt the loop with a
  question instead of taking the default and logging it.
- Orchestrators consume their own context doing work that belongs in
  subagents, then degrade instead of handing off.

docs/human-gates.md gates the _launch_ of execution stages — the spend
and blast-radius discontinuities. Today's behavior additionally makes
the human re-launch every continuation, friction the gates never
intended. The wanted contract: once a human launches, the session
consumes work until nothing is dispatchable, delays human decisions as
far as they'll safely go, and ends with a clear checklist of what only
a human can do next.

## Solution

A session-level exhaustion contract, written into the execution-stage
skills (drain primarily; build and autopilot where noted):

1. **Rolling continuation across the whole queue.** When a worker
   finishes, the orchestrator immediately runs the next loop step; when
   a spec's tasks are exhausted, it moves to the next spec with
   dispatchable work. The session never ends while dispatchable work
   remains anywhere in `specs/`. (Extends the in-flight
   `specs/drain-rolling-window/` top-up — which is per-wave, within one
   spec — across specs and stages.)
2. **Draft intake.** A spec with no `tasks/` and no `Breakdown-ready:`
   marker is not a dead end: the orchestrator runs /critique on it
   (model-invocable; CLAUDE.md's self-chain conditions hold). READY →
   the existing marker + auto-/breakdown path makes it dispatchable in
   the same session. NOT READY → findings are recorded with the spec,
   the spec lands on the exit checklist, and the loop continues with
   other work. Draft task stubs from discovered-work capture route the
   same way via their spec.
3. **Decision deferral.** A mid-loop decision with a reversible default
   takes the default and logs it (what was decided, the default taken,
   how to reverse). Only decisions on the human-gates list
   (irreversible, blast-radius, spend, authority) block — and they
   block the ITEM (`Status: blocked` + reason), never the loop. Drain's
   batch-interview remains the mechanism for questions that must be
   asked, fired once at the end, never per item.
4. **Context self-management.** The orchestrator keeps only the loop;
   consumption (implementation, verification, critique) runs in
   subagents per token-discipline. When the orchestrator's own context
   grows heavy mid-queue, it writes the /handoff file and puts the
   resume command as the first line of the exit checklist, rather than
   degrading in place.
5. **Exit checklist.** The session's final message is a checklist for
   the human: decisions deferred (with the defaults taken), items
   blocked (with what unblocks each), NOT-READY specs (top findings),
   and the exact next commands to run. "Nothing needs you" is a valid
   checklist.

## Requirements

- R1: drain's skill text states the exhaustion contract: never end the
  session while dispatchable work remains in `specs/`; on finishing a
  spec, inventory the next.
- R2: drain's inventory step treats no-tasks, no-marker specs as
  critique-intake work: run /critique; on READY continue through the
  existing auto-/breakdown path in the same session; on NOT READY
  record findings and continue elsewhere.
- R3: The decision-deferral rule (reversible default + log; human-gates
  decisions block the item, never the loop) appears in drain's worker
  handling and in /build.
- R4: The exit checklist is a fixed final-message contract in drain and
  autopilot: deferred decisions, blocked items, NOT-READY specs, next
  commands — each with file paths.
- R5: The heavy-context escape hatch: orchestrator writes /handoff and
  leads the checklist with the resume command instead of continuing
  degraded.
- R6: docs/human-gates.md gains one clarifying line: gates govern
  launch, not continuation — an in-flight session consuming the queue
  it was launched on is inside the gate, and batching deferred
  decisions into the exit checklist is the intended shape.
- R7: Antigravity mirrors (drain/build/autopilot workflows) receive the
  equivalent contract; `.claude-plugin/plugin.json` bumped; paths in
  some task's `Touch:` (CLAUDE.md's mirroring convention).

## Out of scope

- Weakening any human-gates launch gate — this spec changes what
  happens after launch, never who launches.
- Auto-approving irreversible or blast-radius decisions — those still
  block their item.
- Cross-session scheduling (cron/Routines) — exhaustion is
  within-session; resuming is the checklist's job.
- /idea auto-generating new specs from nothing — intake starts at
  existing drafts, not invention.

## Acceptance criteria

- [ ] `grep -qi "dispatchable work remains" .claude/skills/drain/SKILL.md` (R1)
- [ ] drain's inventory step names the critique-intake route:
      `grep -q "Breakdown-ready" .claude/skills/drain/SKILL.md` shows the
      no-marker branch running /critique, not skipping the spec (R2).
- [ ] `grep -qi "reversible default" .claude/skills/drain/SKILL.md && grep -qi "reversible default" .claude/skills/build/SKILL.md` (R3)
- [ ] `grep -qi "checklist" .claude/skills/drain/SKILL.md && grep -qi "checklist" .claude/skills/autopilot/SKILL.md` (R4)
- [ ] `grep -qi "handoff" .claude/skills/drain/SKILL.md` names the
      heavy-context escape (R5).
- [ ] `grep -qi "continuation" docs/human-gates.md` (R6)
- [ ] Antigravity mirrors carry the contract; plugin.json version higher
      than before (R7).
- [ ] Fresh-session test: a fixture queue with one dispatchable task,
      one draft spec (no tasks, no marker), and one task whose worker
      hits a reversible decision — a single /drain launch finishes all
      three lanes and ends with the checklist naming the deferred
      decision (manual, per CLAUDE.md's testing convention).

## Open questions

- Whether autopilot's walk-away contract needs a per-item deferral
  budget (N deferred decisions before it stops anyway) — decide at
  /critique.
