# Task 05: Decision record, fixture e2e, version bump

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
Status: done
Depends on: 01, 02, 03, 04
Priority: P2
Budget: 50 turns
Spec: ../SPEC.md (requirements R7, R8-bump, end-to-end)
Touch: docs/decisions/orchestrator-context.md, .claude-plugin/plugin.json, specs/orchestrator-context/evidence/

## Goal

`docs/decisions/orchestrator-context.md` records the trigger design
(N=4 + degradation override), the cap (10), the research basis with
cross-vendor corroboration (Anthropic + OpenAI + Google per the
2026-07-03 amendment — NOT the stale "Anthropic-only" caveat), the
remaining leg-B gap, and links the research doc + spec. The fixture
end-to-end proves the baton loop: a 6-task fixture spec with
`Relaunch-every: 2`, `DRAIN_RELAUNCH_CMD` pointed at a recorder script,
stubbed workers (trivial acceptance commands) → 2 baton passes recorded,
batons carry done/next + generation, recorder argv matches the documented
command, gen-2 log shows the ritual ran before dispatch, final generation
deletes the baton, all 6 tasks done. plugin.json gets the spec's version
bump.

## Touch

The fixture lives in a temp directory (mktemp), not the repo; only its
evidence lands under specs/orchestrator-context/evidence/. Must NOT
touch: the skill files (tasks 01–04 own them).

## Steps

1. Write the decision record per R7 + the amendment.
2. Build the fixture: temp repo, 6 stub task files, SPEC.md with
   `Relaunch-every: 2` in its header block, recorder script as
   `DRAIN_RELAUNCH_CMD`, stub gen-2 honoring the ritual.
3. Run the fixture drain; capture the assertions above into
   specs/orchestrator-context/evidence/05-e2e.md.
4. Bump `.claude-plugin/plugin.json` minor version; `claude plugin
   validate .`.

## Acceptance

- [x] `test -f docs/decisions/orchestrator-context.md` → exit 0; names N=4, cap 10, cross-vendor corroboration per the amendment, links both docs
      — verifier PASS C1 (evidence/05-decisions-e2e-bump.md): doc names N=4, cap 10, "Anthropic + OpenAI + Google" superseding the stale Anthropic-only caveat, links research doc + SPEC.
- [x] Fixture e2e evidence file records: 2 baton passes, done/next + generation in each baton, recorder argv == documented command, gen-2 ritual-before-dispatch, baton deleted at completion, 6/6 tasks done
      — verifier PASS C2: `bash specs/orchestrator-context/evidence/05-e2e-harness.sh` exit 0, 20/20 assertions; harness faithful to drain reference.md "Baton pass" + SKILL.md step 3a; evidence at evidence/05-e2e.md.
- [x] `python3 -c "import json,sys; v=json.load(open('.claude-plugin/plugin.json'))['version']; sys.exit(0 if v != '0.7.0' else 1)"` → exit 0 (bumped past the drained queue's 0.7.0; adjust if an intervening bump landed)
      — verifier PASS C3: version bumped 0.7.2 → 0.7.3, exit 0.
- [x] `claude plugin validate .` → exit 0
      — verifier PASS C4: `✔ Validation passed`, exit 0.
