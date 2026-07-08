# Work exhaustion: consume the queue until nothing is dispatchable

Status: open
Priority: P1

## Problem

In real usage (maintainer feedback, 2026-07-08) the pipeline stalls
between stages instead of consuming work:

- Sessions stop when a dispatched unit finishes rather than proceeding
  to the next step of the loop (collect the verdict, merge, top up,
  claim the next item).
- Draft specs sit inert until a human manually runs /critique and
  /breakdown — even though /critique is model-invocable and drain
  already auto-invokes /breakdown on `Breakdown-ready: true` specs; the
  missing link is nobody runs the critique step unprompted.
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

1. **Rolling continuation across the launched scope.** When a worker
   finishes, the orchestrator immediately runs the next loop step. The
   scope is drain's launch argument, unchanged; a no-argument launch now
   means the whole `specs/` queue, consumed one spec at a time:
   claim that spec's owner lease, drain it, release the lease, move to
   the next spec with dispatchable work (never more than one lease held;
   the per-spec concurrent-drain refusal and the per-run generations cap
   are unchanged). The session ends only when no spec in scope has
   dispatchable work. (Extends the in-flight `specs/drain-rolling-window/`
   top-up — which is per-wave, within one spec — across the scope.)
2. **Critique intake for draft specs.** A spec in scope with no `tasks/`
   and no `Breakdown-ready:` marker is not a dead end: the orchestrator
   runs /critique on it (model-invocable). READY → the critic-written
   marker + the existing auto-/breakdown path make it dispatchable in
   the same session. NOT READY → findings are recorded with the spec,
   the spec lands on the exit checklist, and the loop continues with
   other work. Draft TASK stubs are explicitly not intake: only a human
   promotes `draft` → `pending` (docs/human-gates.md reason 1, drain's
   existing invariant, both unchanged) — stubs appear on the exit
   checklist as promotion candidates instead.
3. **Decision deferral.** The worker takes a mid-task decision that has
   a reversible default itself — that is the amendment to the worker
   contract's "on ambiguity, stop with verdict DEFERRED": ambiguity
   WITH a reversible default → take the default, keep working, and
   report it in a new fixed `Decisions:` section of the worker's
   verdict report (decision, default taken, how to reverse); drain
   appends each entry to the task file under `## Decisions` — the same
   worker-reports/drain-records split as discovered-work capture, so
   the worker still never edits queue state. Ambiguity with NO
   reversible default, and any decision on the human-gates list
   (irreversible, blast-radius, spend, authority), still stops the
   worker with DEFERRED — and drain's batch interview at exit remains
   how those questions reach the human, once, never per item.
   `Status: blocked` keeps its current meaning (failures needing
   amendment, with no askable question) and is not used for decisions.
   /build (attended) applies the same reversible-default rule, logging
   to the task file's `## Decisions` in its close-out.
4. **Context self-management.** The orchestrator keeps only the loop;
   consumption (implementation, verification, critique) runs in
   subagents per token-discipline. Drain's existing degradation
   response is unchanged and stays first: write `DRAIN-BATON.md` and
   self-relaunch a fresh generation. The /handoff escape applies only
   where the baton cannot: when the generations cap is exhausted, or in
   attended /build — then the session writes the /handoff file and
   leads the exit checklist with the resume command instead of
   continuing degraded.
5. **Exit checklist.** The session's final message is a checklist for
   the human. Drain's sections: deferred decisions awaiting the batch
   interview's answers, defaults taken (from `## Decisions`), blocked
   items (with what unblocks each), NOT-READY specs (top findings),
   draft stubs awaiting promotion, and the exact next commands.
   Autopilot's checklist carries only what autopilot produces: defaults
   taken, its task's blocker if any, and the next command. "Nothing
   needs you" is a valid checklist.

## Requirements

- R1: drain's skill text states the exhaustion contract: never end the
  session while dispatchable work remains in the launched scope; a
  no-argument launch consumes all of `specs/` sequentially under the
  one-lease-at-a-time rule in Solution 1.
- R2: drain's inventory step gains the critique-intake branch for
  no-`tasks/`, no-marker specs exactly as Solution 2 defines, and
  leaves draft-stub promotion human-only.
- R3: The decision-deferral rule lands per Solution 3: the worker
  contract's ambiguity clause is amended (reversible default → take,
  report in the fixed `Decisions:` section; otherwise DEFERRED as
  today); drain appends `Decisions:` entries to the task file's
  `## Decisions`; gate-list decisions route through DEFERRED to the
  batch interview, never `Status: blocked`; /build applies the same
  rule attended.
- R4: The exit checklist is a fixed final-message contract — drain's
  six sections and autopilot's three, per Solution 5, each entry with a
  file path.
- R5: The /handoff escape is scoped per Solution 4: baton first;
  /handoff only on generations-cap exhaustion or in attended /build.
- R6: docs/human-gates.md's final self-chain section is REVISED (not
  appended to): the auto-/breakdown authorization is the adversarial
  READY verdict written by the critic's independent context — whether
  that critique ran in an earlier invocation or in-session during
  drain's critique intake — and gates govern launch, not continuation.
  The current "separate, earlier invocation … before drain ever looks"
  sentence is rewritten so the doc and this mechanism agree.
- R7: Antigravity mirrors (drain/build/autopilot workflows) receive the
  equivalent contract; `.claude-plugin/plugin.json` bumped; paths in
  some task's `Touch:` (CLAUDE.md's mirroring convention).

## Out of scope

- Weakening any human-gates launch gate — this spec changes what
  happens after launch, never who launches.
- Auto-approving irreversible or blast-radius decisions — those still
  stop the item's worker and wait for the batch interview.
- Auto-promoting draft task stubs — human-only, unchanged.
- Cross-session scheduling (cron/Routines) — exhaustion is
  within-session; resuming is the checklist's job.
- /idea auto-generating new specs from nothing — intake starts at
  existing draft specs, not invention.

## Acceptance criteria

- [ ] `grep -qi "dispatchable work remains" .claude/skills/drain/SKILL.md` (R1)
- [ ] `grep -qi "critique intake" .claude/skills/drain/SKILL.md` — the
      literal branch name from Solution 2, absent from today's text (R2).
- [ ] `grep -qi "reversible default" .claude/skills/drain/SKILL.md && grep -qi "reversible default" .claude/skills/build/SKILL.md` (R3)
- [ ] `grep -q "Decisions:" .claude/skills/drain/SKILL.md` — the fixed
      report section exists in the worker contract (R3).
- [ ] `grep -qi "checklist" .claude/skills/drain/SKILL.md && grep -qi "checklist" .claude/skills/autopilot/SKILL.md` (R4)
- [ ] `grep -qi "generations cap" .claude/skills/drain/SKILL.md` appears
      in the same passage that names /handoff (R5; manual read of the
      passage confirms baton-first).
- [ ] `grep -qi "continuation" docs/human-gates.md` and the reason-2
      self-chain section no longer contains "before drain ever looks"
      verbatim (R6).
- [ ] Antigravity mirrors carry the contract; plugin.json version higher
      than before (R7).
- [ ] Fresh-session test: a fixture queue with one dispatchable task,
      one draft spec (no tasks, no marker), one draft task stub, and one
      task whose worker hits a reversible decision — a single
      no-argument /drain launch finishes the first two lanes, leaves the
      stub a draft, and ends with a checklist naming the taken default
      and the stub as a promotion candidate (manual, per CLAUDE.md's
      testing convention).

## Open questions

- Whether autopilot's walk-away contract needs a per-item deferral
  budget (N defaults taken before it stops anyway) — decide at
  /breakdown; default is no budget (defaults are reversible by
  definition, and the checklist surfaces every one).
