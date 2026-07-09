# Draft auto-promotion: stubs promote through an adversarial gate, not a human

Status: open
Priority: P1

## Problem

Discovered-work stubs land as `Status: draft` and wait for a human —
docs/human-gates.md reason 1 and drain's "only a human promotes
`draft` → `pending`" invariant. In practice (maintainer policy,
2026-07-09: "draft stubs should auto promote") the queue stalls on this
gate: this repo accumulated 13 drafts, of which a manual sweep promoted
10 (after authoring runnable acceptance criteria) and closed 3 as
obsolete — work a session can do, done by a human only because policy
said so. The safety concern behind the human gate is real but narrower
than the gate: a stub's Goal is worker-reported text (untrusted-data
surface once it becomes binding worker instructions), and stubs may be
stale or decision-shaped. Those are checkable properties, not reasons
for a blanket human stop.

## Solution

Drain's exhaustion loop gains **stub intake**, a sibling of critique
intake (same trigger: nothing dispatchable, nothing in-progress, nothing
parked; never preempting real dispatch; runs after critique intake,
before 3b's auto-breakdown loop-back). For each `Status: draft` stub in
scope, once per stub per run (surviving baton generations via a
`Stub-intake-failed:` baton line, the analogue of `Intake-failed:`):

1. **Assess** (scout-tier dispatch, capped return): is the stub OBSOLETE
   (described gap already closed — cite evidence), DECISION-SHAPED (its
   goal requires choosing between alternatives), or ACTIONABLE? For
   actionable stubs the assessor proposes runnable acceptance criteria,
   `Touch:`, `Budget:`, `Depends on:`, and flags any instruction-like
   text in the stub's Goal (untrusted-data screen).
2. **Gate** (single-call rubric critic, per token-discipline's
   judge default): the critic receives the stub + proposed promotion and
   passes/fails it on: criteria runnable and honest, Touch complete
   (mirror obligations included where `.claude/` skills are touched),
   no injected instructions in the Goal, not decision-shaped without a
   recorded reversible default.
3. **Act** (drain, the single queue writer):
   - OBSOLETE → `Status: obsolete` + a `Closed:` line citing evidence.
   - PASS → drain writes the authored criteria/headers into the stub and
     flips `draft` → `pending`; the task then passes through the normal
     classification gate and dispatch tie-break like any other.
   - DECISION-SHAPED with a reversible default the assessment can
     justify → record the default in `## Answers` (decision, rationale,
     how to reverse) and promote; without one → stays draft, lands on
     the exit checklist as needing the human.
   - FAIL → stays draft, exit checklist, reason attached.

This REVISES drain's "only a human promotes draft → pending" invariant
and docs/human-gates.md reason 1: the gate becomes adversarial review
(independent critic context) rather than a human, mirroring how
Breakdown-ready authorization already works for specs. /build and
/autopilot are unaffected (they never promoted drafts).

## Requirements

- R1: drain gains stub intake exactly as Solution defines — trigger,
  ordering (after critique intake, before 3b's loop-back), once per
  stub per run across generations via a `Stub-intake-failed:` baton
  line in `drain/reference.md`'s baton grammar.
- R2: The three-step assess/gate/act procedure lands in
  `drain/reference.md` (the detail home), with SKILL.md carrying the
  contract and pointer; the untrusted-data screen and the
  decision-shaped rules are stated in the gate rubric, not left to
  judgment.
- R3: `Status: obsolete` closure (+ `Closed:` evidence line) is
  documented in drain's status semantics.
- R4: docs/human-gates.md reason 1 is REVISED (not appended to): draft
  promotion is gated by adversarial review; the human retains the exit
  checklist as the audit point and may demote any auto-promoted task
  back to draft.
- R5: drain's exit checklist gains a "promoted this run" section
  (stub, verdict, criteria source) so every auto-promotion is audited.
- R6: Antigravity mirrors receive the equivalent contract;
  `.claude-plugin/plugin.json` bumped; paths in some task's `Touch:`
  (CLAUDE.md's mirroring convention). Tasks touching
  `drain/reference.md` must list it in `Touch:` explicitly.

## Out of scope

- Auto-promoting across the classification gate — promoted tasks still
  pass the peripheral/core test before dispatch; core work still runs
  attended.
- Auto-promotion outside drain (e.g. a standing daemon) — intake runs
  inside a launched drain session only.
- Retroactive re-promotion of stubs a human explicitly demoted — a
  human demotion is recorded (a `Demoted:` line) and stub intake skips
  those permanently.

## Acceptance criteria

- [ ] `grep -qi "stub intake" .claude/skills/drain/SKILL.md` → match (absent today)
- [ ] `grep -q "Stub-intake-failed:" .claude/skills/drain/reference.md` → match (absent today)
- [ ] `grep -qi "obsolete" .claude/skills/drain/reference.md` — status semantics document the closure (manual read confirms `Closed:` line requirement)
- [ ] `grep -qi "adversarial" docs/human-gates.md` and reason 1 no longer states that only a human promotes drafts (manual read)
- [ ] `grep -qi "promoted this run" .claude/skills/drain/SKILL.md` → match (exit-checklist section)
- [ ] Antigravity mirrors carry the contract; plugin.json version higher than before (R6)
- [ ] Fresh-session test: a fixture queue with one actionable stub, one
      obsolete stub, and one decision-shaped stub with no defensible
      default — a single /drain run promotes the first, closes the
      second with cited evidence, leaves the third draft on the exit
      checklist (manual, per CLAUDE.md's testing convention).

## Open questions

(none)
