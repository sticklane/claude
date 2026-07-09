# Work exhaustion: consume the queue until nothing is dispatchable

Status: open
Priority: P1
Breakdown-ready: true

## Problem

In real usage (maintainer feedback, 2026-07-08) the pipeline stalls
between stages instead of consuming work:

- Sessions stop when a dispatched unit finishes rather than proceeding
  to the next step of the loop (collect the verdict, merge, top up,
  claim the next item).
- Draft specs sit inert until a human manually runs /critique and
  /breakdown — even though /critique is model-invocable and drain
  already auto-invokes /breakdown on marker-bearing specs; the missing
  link is nobody runs the critique step unprompted.
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
skills (drain primarily — both `drain/SKILL.md` and `drain/reference.md`,
which carries the actual worker prompt; build and autopilot where noted):

1. **Rolling continuation across the launched scope.** When a worker
   finishes, the orchestrator immediately runs the next loop step. The
   scope is drain's launch argument, unchanged; a no-argument launch now
   means the whole `specs/` queue, consumed one spec at a time. Lease
   discipline for the sequential walk: claim a spec's `DRAIN-OWNER.md`
   when its dispatch begins, and release it (delete, committed) when
   that spec has nothing left to dispatch — its remaining tasks are
   done, deferred, blocked, failed, or draft — before moving to the next
   spec. Deferred questions live in committed task files, so nothing
   needs the lease held while the session works elsewhere; if the
   end-of-session interview (Solution 5) turns a deferred task back to
   `pending`, drain re-claims that spec's lease before re-dispatching,
   exactly like a fresh claim. At most one DISPATCH lease is held at a
   time; the short-lived second lease 3b already takes while
   auto-breaking-down another spec (claim → act → release) is unchanged
   and may transiently overlap, as may critique intake's identical
   claim (Solution 2). The per-spec concurrent-drain refusal and the
   per-run generations cap are unchanged. The session ends only when no
   spec in scope has dispatchable work. (Extends the in-flight
   `specs/drain-rolling-window/` top-up — per-wave, within one spec —
   across the scope.)
2. **Critique intake for draft specs.** Fires only at the exhaustion
   trigger — the same "nothing dispatchable, nothing in-progress,
   nothing parked" check that gates 3b, evaluated immediately BEFORE 3b
   (intake writes the marker 3b consumes) — and never preempts a
   dispatchable task. A spec in scope with no `tasks/` and no
   `Breakdown-ready:` header is intake work: claim that spec's owner
   lease first (the same claim → act → release procedure 3b uses on its
   target, refusing and skipping on a lost race), then run /critique on
   it (model-invocable). READY → the critic-written marker + the
   existing auto-/breakdown path make it dispatchable in the same
   session. NOT READY → findings are recorded with the spec, the spec
   lands on the exit checklist, the lease is released, and the loop
   continues. Attempt each spec's intake at most once per run, surviving
   baton generations the same way 3b's attempted-and-failed set does.
   Draft TASK stubs are explicitly not intake: only a human promotes
   `draft` → `pending` (docs/human-gates.md reason 1, drain's existing
   invariant, both unchanged) — stubs appear on the exit checklist as
   promotion candidates instead.
3. **Decision deferral.** The worker takes a mid-task decision that has
   a reversible default itself — that is the amendment to the worker
   prompt's ambiguity clause, which lives in `drain/reference.md`'s
   "Worker prompt" ("do NOT guess … stop with verdict DEFERRED"):
   ambiguity WITH a reversible default → take the default, keep
   working, and report it in a new fixed `Decisions:` section of the
   worker's verdict report (decision, default taken, how to reverse).
   The report-format paragraph in the same section (whose closing
   sentence currently counts "these two fixed sections") is revised to
   name three. Drain appends each entry to the task file under
   `## Decisions` — the same worker-reports/drain-records split as
   discovered-work capture, so the worker still never edits queue
   state. Ambiguity with NO reversible default, and any decision on the
   human-gates list (irreversible, blast-radius, spend, authority),
   still stops the worker with DEFERRED — and drain's batch interview
   at exit remains how those questions reach the human, once, never per
   item. `Status: blocked` keeps its current meaning (failures needing
   amendment, with no askable question) and is not used for decisions.
   /build (attended) applies the same reversible-default rule, logging
   to the task file's `## Decisions` in its close-out. Autopilot's
   unattended run inherits the rule with no separate edit — it
   dispatches with the amended /build procedure — and its checklist's
   "defaults taken" line reads the same `## Decisions` section.
4. **Context self-management.** The orchestrator keeps only the loop;
   consumption (implementation, verification, critique) runs in
   subagents per token-discipline. Drain's existing degradation
   response is unchanged and stays first: write `DRAIN-BATON.md` and
   self-relaunch a fresh generation. The /handoff escape applies only
   where the baton cannot: when the generations cap is exhausted, or in
   attended /build — then the session writes the /handoff file and
   leads the exit checklist with the resume command instead of
   continuing degraded.
5. **Exit checklist.** Fires once per session, at scope exhaustion,
   fused with drain's batch interview: the interview asks every
   deferred question aggregated across ALL specs drained this session
   (as today, gated on `Status: deferred`), and the session's final
   message is a checklist for the human. Drain's sections: deferred
   questions still unanswered, defaults taken (from `## Decisions`),
   blocked items (with what unblocks each), NOT-READY specs (top
   findings), draft stubs awaiting promotion, and the exact next
   commands. Autopilot's checklist carries only what autopilot
   produces: defaults taken, its task's blocker if any, and the next
   command. "Nothing needs you" is a valid checklist.

## Requirements

- R1: drain's skill text states the exhaustion contract: never end the
  session while dispatchable work remains in the launched scope; a
  no-argument launch consumes all of `specs/` sequentially under
  Solution 1's lease discipline (release on nothing-left-to-dispatch,
  re-claim on re-dispatch, transient 3b/intake overlap allowed).
- R2: drain gains the critique-intake branch exactly as Solution 2
  defines — exhaustion-triggered, evaluated before 3b, lease-claimed,
  once per run across generations — and leaves draft-stub promotion
  human-only. Cross-generation persistence adds an `Intake-failed:`
  line to the baton grammar in `drain/reference.md` (the analogue of
  `Breakdown-failed:`), so the intake task's `Touch:` must list
  `drain/reference.md` too (same Touch rule as R3).
- R3: The decision-deferral rule lands per Solution 3, in BOTH drain
  files: `drain/reference.md`'s worker-prompt ambiguity clause and
  report format (the fixed `Decisions:` section; the "two fixed
  sections" sentence revised) and `drain/SKILL.md`'s verdict handling
  (append entries to the task file's `## Decisions`; gate-list
  decisions route through DEFERRED to the batch interview, never
  `Status: blocked`). /build applies the same rule attended. The
  implementing task's `Touch:` must list `drain/reference.md` alongside
  `drain/SKILL.md` — an unlisted path silently ships the worker prompt
  unchanged (CLAUDE.md's Touch rule).
- R4: The exit checklist is a fixed final-message contract — drain's
  six sections and autopilot's three, per Solution 5, each entry with a
  file path; one interview + one checklist per session at scope
  exhaustion.
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
- [ ] `grep -qi "reversible default" .claude/skills/drain/reference.md && grep -qi "reversible default" .claude/skills/build/SKILL.md` (R3)
- [ ] `grep -q "Decisions:" .claude/skills/drain/reference.md` — the
      fixed report section exists in the worker prompt — and the
      section count is revised:
      `grep -q "three fixed sections" .claude/skills/drain/reference.md`
      (absent from today's text, so the check fails until the sentence
      is actually rewritten) (R3).
- [ ] `grep -q "## Decisions" .claude/skills/drain/SKILL.md` — drain
      records what workers report (R3).
- [ ] `grep -qi "checklist" .claude/skills/drain/SKILL.md && grep -qi "checklist" .claude/skills/autopilot/SKILL.md` (R4)
- [ ] `grep -q "/handoff" .claude/skills/drain/SKILL.md` — absent from
      today's text — in the same passage as the generations cap (R5;
      manual read confirms baton-first ordering).
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

## Parallelization

Tasks 01, 02, and 03 have pairwise-disjoint `Touch:` lists, and every
shared design choice (the `Decisions:` report section, the `## Decisions`
task-file section, the `Intake-failed:` baton line, DEFERRED routing for
gate-list decisions) is pinned in this spec, so no member resolves an open
choice — the decision-coupling test passes. Task 04 mirrors the landed
result and closes the spec, so it depends on all three. Group-line grammar
per specs/drain-rolling-window/SPEC.md's Parallelization section.

- Group: 01, 02, 03
