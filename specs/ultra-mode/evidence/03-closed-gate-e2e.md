# Closed-gate end-to-end: /critique single-critic path (task 03)

Records the closed-gate half of SPEC.md's end-to-end acceptance criterion:
`/critique` in a no-runtimes fixture install runs the single-critic path with
no ultra mention. The open-gate (panel) half is manual-pending — see below.

Ref: `specs/ultra-mode/SPEC.md` (end-to-end criterion, R2, R6, R9).

## Part A — structural gate proof (deterministic, re-runnable)

Harness: `specs/ultra-mode/evidence/03-closed-gate-harness.sh`
Re-run: `bash specs/ultra-mode/evidence/03-closed-gate-harness.sh` → exit 0.
It builds a throwaway mktemp install carrying only critique/SKILL.md and
deliberately no `runtimes/`, then asserts the ultra path is unreachable there:

```
PASS  fixture install has no runtimes/ dir (gate condition-2 unsatisfiable)
PASS  no '## Orchestration (ultra)' profile section present -> panel template unreachable
PASS  single-critic default path ('Spawn the critic agent') present in fixture skill
PASS  Ultra path text states single-critic is the only path when profile is silent
PASS  every 'ultra' mention gated within +/-3 lines of 'active runtime profile'
PASS  break-test: removing the marker phrase makes the gate detector fire (load-bearing)

closed-gate-harness: OK — single-critic path is the only reachable path in a no-runtimes install
```

The two-condition gate (SPEC.md R2, critique/SKILL.md "## Ultra path") needs
BOTH ultracode opted in AND "the active runtime profile documents an
orchestration section". A no-runtimes install fails condition two, and the
break-test confirms the marker phrase is load-bearing, not incidental.

## Part B — real single-critic run (behavioral)

A live `critic` agent was spawned once against a fixture spec written to a
scratch dir with no `runtimes/` present. Fixture plants:

- **Contradiction:** R1 ("writes update backing store synchronously before
  returning") vs R2 ("writes MUST return immediately... flush asynchronously").
- **Un-runnable acceptance check:** `- [ ] The cache "feels fast" to users
  under normal load.`
- **Refutable bait:** a vacuous `bash tests/run.sh` check (trivially green).

Observed behavior:

- **Exactly one critic** was dispatched (single-critic path — no 3–5 critic
  panel, no Workflow run). This is the closed-gate default.
- **Both real plants found:** finding #1 quoted the R1/R2 MUST/MUST
  contradiction (confidence 98) as the NOT-READY blocker; finding #2 flagged
  the "feels fast" criterion as having no runnable check (confidence 97). The
  bait check was correctly characterized as vacuous, not asserted as a real bug.
- **Verdict relayed verbatim** in ranked order (NOT READY) per the skill's
  step 2 — no softening.
- **No "ultra" mention** anywhere in the critic's output: the panel path,
  verify-vote phase, and any ultra vocabulary were absent, as required when the
  gate is closed.

## Result

PASS (closed-gate half). Single-critic path is the only reachable path in a
no-runtimes install and the live run exercised it end-to-end with no ultra
leakage.

## Open-gate (panel) half — MANUAL-PENDING

Not run here. Reason: the executing worker is unattended and the Workflow
(ultracode) tool is not available to it, so the panel gate cannot be opened —
opting into ultracode requires the Workflow tool. The orchestrator, which has
the Workflow tool, runs the open-gate panel probe post-merge: `/critique`
against a three-plant fixture with ultracode active, asserting a Workflow run
is observable, both real plants are found, and the verify-vote phase drops any
refuted finding. Per the task's own acceptance wording this is recorded as
manual-pending, not faked.
