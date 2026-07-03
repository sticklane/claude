# Task 03: Evals runner parameterization (RUNNER_CMD / EVALS_ROOT)

Status: pending
Depends on: ../../review-fixes/tasks/06-evals-runner-robustness.md
Budget: 30 turns
Spec: ../SPEC.md (requirement R6)

## Goal

Make the evals harness runtime-portable: `evals/run.sh` gains two
environment overrides (`RUNNER_CMD` for the headless command, `EVALS_ROOT`
for scenario discovery), and a shipped stub CLI plus a selftest prove the
pass/fail plumbing works with a non-Claude command against a throwaway
scenario tree — never touching the committed evalsets. With both vars
unset, behavior is byte-identical to today.

## Touch

- evals/run.sh
- evals/stub-cli.sh (new)
- evals/runner-selftest.sh (new)
- Cross-spec: also edited by review-fixes — see specs/QUEUE.md

## Steps

1. `evals/run.sh`: honor `RUNNER_CMD` — when set, execute it word-split,
   inside the existing `cd "$EVAL_DIR"` + `timeout 900` wrapper, with the
   scenario's prompt appended as the final argument; export the
   scenario's resolved allowlist to the child as `ALLOWED_TOOLS`
   (document in a comment that custom runners may consume or ignore it).
   Document next to the override that, because execution happens inside
   the fixture dir, `RUNNER_CMD`'s first word must be absolute or
   PATH-resolvable. When unset, the existing
   `claude -p … --allowed-tools …` invocation is byte-identical.
2. `evals/run.sh`: honor `EVALS_ROOT` — scenario discovery scans
   `$EVALS_ROOT/<skill>/<NN-name>/` instead of the toolkit's `evals/`;
   default is today's location. Skill provisioning still sources from the
   toolkit checkout.
3. Create `evals/stub-cli.sh` (executable): a no-model shell stub that
   reads its final argument (the prompt) and writes the fixture artifact
   the selftest's assert expects.
4. Create `evals/runner-selftest.sh` (executable): build a throwaway
   scenario tree under `mktemp -d` naming a real, small toolkit skill
   (e.g. handoff) so provisioning succeeds; invoke
   `EVALS_ROOT=<tmp> RUNNER_CMD="${RUNNER_CMD:-$(pwd)/evals/stub-cli.sh}" ./evals/run.sh <skill>`;
   assert the PASS line with exit 0, then a deliberately failing assert
   producing the FAIL line with exit 1. The selftest scenario must never
   be discoverable by a plain `./evals/run.sh` (it lives only in the temp
   tree).
5. Run the acceptance commands below, including the no-behavior-change
   check on the committed breakdown evalset.
6. Do NOT bump `.claude-plugin/plugin.json` — the single batch version
   bump (R10) is owned by global task 99 in specs/review-fixes.

## Acceptance

- [ ] `grep -q "RUNNER_CMD" evals/run.sh && grep -q "EVALS_ROOT" evals/run.sh && grep -q "ALLOWED_TOOLS" evals/run.sh && bash -n evals/run.sh` → exit 0 (R6)
- [ ] `test -x evals/stub-cli.sh && test -x evals/runner-selftest.sh && bash -n evals/stub-cli.sh && bash -n evals/runner-selftest.sh` → exit 0 (R6)
- [ ] `./evals/runner-selftest.sh` → exits 0 on a machine with no model access (uses the shipped stub by default; both the PASS and FAIL plumbing paths asserted) (R6 end-to-end)
- [ ] End to end: `./evals/run.sh breakdown` → still passes with both env vars unset (no behavior change for the Claude default), and `./evals/runner-selftest.sh` → proves a non-Claude command drives the same harness without touching the committed evalsets
