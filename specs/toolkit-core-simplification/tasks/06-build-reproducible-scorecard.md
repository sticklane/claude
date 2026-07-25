# Task 06: build the reproducible outcome and cost scorecard

<!-- Task state is canonical in bd. The Status line is frozen display and is not edited by workers. -->

Status: pending
Depends on: 05
Priority: P1
Budget: 44 turns
Spec: ../SPEC.md (requirement R6)
Touch: agentprof/cmd_skillcheck.go, agentprof/cmd_skillcheck_trigger.go, agentprof/cmd_skillcheck_test.go, agentprof/cmd_skillcheck_trigger_test.go, scripts/report-toolkit-outcomes.py, tests/test_agentic_scorecard.py, tests/inventory/06-scorecard.json, specs/toolkit-core-simplification/surface-inventory/06-scorecard.json

## Goal

Freeze versioned skill-eligibility judgments and compute every R6 numerator,
denominator, distribution, join, and unknown rate from covered raw inputs.
Older or partially covered arbitrary windows must fail explicitly; monthly
aggregates are immutable reports, not lossy recomputation inputs.

## Touch

Reuse agentprof's existing skillcheck classes and cost samples. Do not add
causal productivity claims or silently price unknown models.

## Steps

1. Write golden fixtures for adoption, verified outcomes, finding
   fingerprints, prevention linkage, delivery percentiles, discovery,
   marginal cost, retries/reopens, both unknown rates, and source coverage.
2. Persist one versioned eligibility/trigger judgment per session and skill,
   reusing it unchanged on rerun.
3. Implement the fixed-window scorecard and full-calendar monthly report with
   formula version and input hashes.

## Acceptance

- [ ] `python3 -m pytest tests/test_agentic_scorecard.py -q` → every R6 formula matches golden numbers and uncovered windows fail with exact missing ranges (L2).
- [ ] `cd agentprof && go test ./... -run 'Skillcheck|Trigger'` → frozen judgment reuse and version/hash fields pass (L2).
- [ ] `bash scripts/check.sh` → Python and Go scorecard changes pass the full inventoried suite (L3).
