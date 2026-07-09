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
   actionable stubs the assessor AUTHORS the promotion text: a fresh,
   neutral Goal written in its own words (the worker-reported original
   is retained only as quoted data under an `## Original report`
   blockquote — it never remains the task's binding text), plus runnable
   acceptance criteria, `Touch:`, `Budget:`, `Depends on:`.
   Before any model reads the stub as a candidate, a DETERMINISTIC
   screen runs: a stub whose Goal matches instruction-shaped patterns
   (the screen script's pinned regex list — imperatives addressed to an
   agent, "ignore/disregard … instructions", tool-invocation directives,
   absolute paths outside the repo) is refused promotion outright this
   run and lands on the exit checklist flagged for a human — never
   assessed, never gated, so promotion of injectable text can't rest on
   a model's judgment of it.
2. **Gate** (single-call rubric critic, per token-discipline's
   judge default): the critic receives the stub + the ASSESSOR-AUTHORED
   promotion and passes/fails it on: criteria runnable and honest, Touch
   complete (mirror obligations included where `.claude/` skills are
   touched), the authored Goal faithful to the original's intent without
   carrying its phrasing, and not decision-shaped without a recorded
   reversible default. OBSOLETE verdicts pass through this same gate —
   the critic must confirm the cited closing evidence before a stub is
   dropped, because closure discards work and deserves the second
   opinion at least as much as promotion does.
3. **Act** (drain, the single queue writer):
   - OBSOLETE (gate-confirmed) → `Status: obsolete` + a `Closed:` line
     citing the evidence the gate checked.
   - PASS → drain writes the authored Goal, criteria, and headers into
     the stub (original Goal preserved as the quoted block) and flips
     `draft` → `pending`; the task then passes through the normal
     classification gate and dispatch tie-break like any other.
   - DECISION-SHAPED with a reversible default the assessment can
     justify → record the default in `## Answers` (decision, rationale,
     how to reverse) and promote; without one → stays draft, lands on
     the exit checklist as needing the human.
   - FAIL → stays draft, exit checklist, reason attached.

This REVISES drain's "only a human promotes draft → pending" invariant
and docs/human-gates.md **reason 4** ("a hard mechanism beats a soft
rule where injection could escalate") — the reason that actually
grounds the draft gate; drain's existing citations of "reason 1" for
this gate (drain/SKILL.md and drain/reference.md both cite it) are
themselves mis-aimed at the spend rationale and get corrected in the
same change. The hard mechanism is preserved, relocated: the
deterministic injection screen plus mandatory Goal re-authoring are the
hard layer (untrusted text never becomes binding instructions), and the
critic gate is the judgment layer on top — mirroring how
Breakdown-ready authorization already works for specs. /build and
/autopilot are unaffected (they never promoted drafts).

## Requirements

- R1: drain gains stub intake exactly as Solution defines — trigger,
  ordering (after critique intake, before 3b's loop-back), once per
  stub per run across generations via a `Stub-intake-failed:` baton
  line in `drain/reference.md`'s baton grammar.
- R2: The three-step assess/gate/act procedure lands in
  `drain/reference.md` (the detail home), with SKILL.md carrying the
  contract and pointer. The deterministic screen ships as a runnable
  script (`.claude/skills/drain/screen-stub.sh` or equivalent) with its
  regex list pinned in the file, so the screen is testable without a
  model; the decision-shaped rules are stated in the gate rubric, not
  left to judgment.
- R3: `Status: obsolete` closure (+ `Closed:` evidence line,
  gate-confirmed) is documented in drain's status semantics.
- R4: docs/human-gates.md **reason 4** is REVISED (not appended to):
  draft promotion moves from human-only to hard-screen + re-authored
  Goal + adversarial review; the human retains the exit checklist as
  the audit point and may demote any auto-promoted task back to draft
  (a `Demoted:` line stub intake permanently respects). Drain's two
  mis-aimed "reason 1" citations for the draft gate (in
  `drain/SKILL.md` and `drain/reference.md`) are corrected to reason 4
  in the same change.
- R5: drain's exit checklist gains a "promoted this run" section
  (stub, verdict, criteria source) so every auto-promotion is audited —
  and the checklist's pinned "six-section" count text in
  `drain/SKILL.md` is bumped to seven in the same edit.
- R6: Antigravity mirrors receive the equivalent contract;
  `.claude-plugin/plugin.json` bumped; paths in some task's `Touch:`
  (CLAUDE.md's mirroring convention). Tasks touching
  `drain/reference.md` must list it in `Touch:` explicitly.
- R7: Every standing manual-promotion statement is revised in the same
  change, enumerated here so a task's `Touch:` can carry them all
  (quoted by phrase — line numbers move while work-exhaustion tasks are
  in flight): reference.md's "**Promotion is manual.**" paragraph, its
  "Drain never writes a draft's `Status:`, not even on an interview
  yes" sentence, its status-table "promoted manually" row, SKILL.md's
  "only a human promotes `draft` → `pending`" statements (inventory
  step and discoveries paragraph), and the critique-intake section's
  "Draft TASK stubs are explicitly not intake … promotion candidates"
  passage (which becomes a pointer to stub intake). A grep sweep for
  "only a human promotes" and "Promotion is manual" over `.claude/`
  must come back empty after the change.

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
- [ ] The deterministic screen script exists, is executable, and refuses
      a fixture stub containing "ignore previous instructions" while
      passing a clean fixture stub (two-line test run, cited) (R2)
- [ ] `grep -qi "obsolete" .claude/skills/drain/reference.md` — status semantics document the gate-confirmed closure (manual read confirms `Closed:` line requirement)
- [ ] `grep -qi "adversarial" docs/human-gates.md` → match, and reason 4's revised text names the hard screen + re-authored Goal (manual read of reason 4, not reason 1) (R4)
- [ ] `grep -rn "reason 1" .claude/skills/drain/` → no hit that cites reason 1 for the draft gate (R4)
- [ ] `grep -rEi "only a human promotes|Promotion is manual" .claude/skills/` → no matches (R7)
- [ ] `grep -qi "promoted this run" .claude/skills/drain/SKILL.md` → match, and the exit-checklist count text says seven (R5)
- [ ] Antigravity mirrors carry the contract; plugin.json version higher than before (R6)
- [ ] Fresh-session test: a fixture queue with one actionable stub, one
      obsolete stub, and one decision-shaped stub with no defensible
      default — a single /drain run promotes the first, closes the
      second with cited evidence, leaves the third draft on the exit
      checklist (manual, per CLAUDE.md's testing convention).

## Open questions

(none)
