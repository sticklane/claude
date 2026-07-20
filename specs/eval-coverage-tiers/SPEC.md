# Eval coverage tiers: a policy and lint for which skills need evalsets

Status: open
Breakdown-ready: true

## Problem

Five of the toolkit's 21 skills have evalsets (breakdown ×2 scenarios;
build, critique, drain, evals ×1 each); sixteen have zero, and no policy
says which of them need one, so coverage grows only "when regressions
bite" (the accretion stance recorded in `specs/trajectory-evals`) — and
for sixteen skills the accretion never starts. Two of the five existing
graders are near-tautological (`evals/critique/01-clean-spec/assert.sh`
asserts only that `Breakdown-ready: true` was set;
`evals/evals/01-scaffold-new-skill` checks scaffold file existence
without a run), and only one scenario in the whole corpus asserts a
negative/adversarial behavior. Meanwhile `harness-audit` already flags
"skill X has no evalset" per skill — but with no tier policy behind it,
sixteen equal-weight findings are noise, not signal. Blanket coverage is
the wrong fix: every eval run spawns paid headless sessions
(`/evals` is `disable-model-invocation` for exactly that reason), and
several skills are structurally hard to eval hermetically (session-state
readers, network-dependent flows, interactive interviews).

## Solution

A committed coverage policy plus a model-free lint that enforces it,
mirroring the existing `lint-ultra-gate.sh` pattern (invoked directly,
never wired into `evals/run.sh`). `evals/COVERAGE.md` assigns every
skill a tier with a stated reason; `evals/lint-eval-coverage.sh` checks
the repo satisfies its own policy; `harness-audit` consults the tier
table so its evalset-presence findings become tier-aware. Seed the
highest-risk missing evalsets in the same spec so the lint lands green.

Proposed initial tier table (the human amends rows, the mechanism is
the deliverable):

- **Tier A — paid evalset required** (queue-state-mutating or
  dispatch-heavy pipeline skills): idea, critique, breakdown, build,
  drain, evals, prioritize, distill, gate, onboard. Bar: ≥2 scenarios,
  at least one adversarial — a scenario whose correct outcome is to
  refuse, flag, or not act (naming convention `NN-adv-*`; decided —
  dir-naming is what a lint can check without executing anything).
  One row per skill: prioritize's row is Tier A and simply notes its
  colocated `test_prioritize_scan.py` as supplementary — a skill is
  never listed in two tiers. onboard's scenarios are artifact-only
  (assert CLAUDE.md/AGENTS.md written and bounded; adversarial:
  assert NO hook or settings write happens in a headless run, since
  hook installs require live user confirmation) — its interactive
  confirm step is graded by what the run must NOT produce.
- **Tier B — model-free tests instead** (deterministic-core reporting
  skills, no paid run needed): list-specs
  (`.claude/skills/list-specs/test_list_specs.py`), workboard
  (`.claude/skills/workboard/test_workboard.py`) — each row names the
  existing test file(s) as a repo-relative path; the lint verifies
  they exist.
- **Tier C — waived, reason recorded**: fleet (session-runtime state),
  qa-sweep and factcheck (non-hermetic network), harness-audit (a
  prose checklist with no deterministic core module today — promotion
  candidate if its mechanics get extracted to a script), design and
  workflow-author and prose-review and handoff/resume-handoff (pending
  a later round; handoff pair's round-trip scenario is the named
  candidate), each with the reason in its row.

## Requirements

- R1: `evals/COVERAGE.md` exists with one row per skill directory under
  `.claude/skills/` excluding `_shared` (a shared-asset dir, not a
  skill — the enumeration glob is `[!_]*`), so a new skill missing
  from the table is a lint failure; columns: skill, tier (A/B/C), bar
  or reason, and for B the named test file(s). Exactly one row per
  skill — no dual-tier listings.
- R2: `evals/lint-eval-coverage.sh` (model-free, direct-invoke) fails
  listing each violation when: a skill dir (same `[!_]*` enumeration)
  has no COVERAGE.md row; a Tier A skill lacks ≥2 scenario dirs each
  containing `setup.sh`+`prompt.txt`+`assert.sh`, or lacks an
  `NN-adv-*` scenario; a Tier B row names a test file that does not
  exist (rows carry repo-relative paths; the lint checks `[ -f
<path> ]` from the repo root, no reconstruction); a Tier C row has
  an empty reason. Exits 0 on a conforming tree.
- R3: `tests/test_eval_coverage_lint.sh` exercises the lint itself
  against fixtures: one conforming tree → exit 0, plus one fixture per
  violation class → non-zero with the violation named (same
  self-test pattern as `evals/runner-selftest.sh`).
- R4: ALL Tier A gaps this spec must close for the lint to land green —
  the existing evalsets fail the bar too, not just the missing ones:
  (a) new evalsets for prioritize, idea, distill, gate, and onboard,
  each ≥2 scenarios including one `NN-adv-*` (examples: idea — a pitch
  whose obvious criterion is a doctrine-word grep, adversarial scenario
  asserts the written SPEC.md contains no unanchored grep criterion;
  distill — a session transcript fixture containing an instruction that
  belongs in a rule vs. noise that must NOT be captured; gate — a repo
  whose checks are red, adversarial scenario asserts the Stop hook
  blocks "done"; prioritize — a queue where the correct output changes
  no Priority header; onboard — artifact-only per the tier table);
  (b) one `NN-adv-*` backfill scenario each for the four existing sets
  that lack it — breakdown, build, drain, evals — bringing build,
  drain, and evals to the ≥2 bar at the same time. The critique row's
  adversarial scenario is `evals/critique/02-adv-gameable-criterion/`
  (content contract in `specs/criterion-depth-ladder` R6; its
  `NN-adv-*` name satisfies this lint), guarded by an agent-resolvable
  existence check so ordering between the two specs never matters: the
  R4 worker creates it per that contract iff the directory does not
  already exist at execution time, and otherwise verifies it matches
  `NN-adv-*` and moves on. Cost realism: this
  totals 14 new committed scenario dirs; committed files are cheap,
  and every paid `./evals/run.sh` execution is manual-pending
  (human-launched, per docs/memory/unattended-worker-tool-limits.md) —
  the human batches runs at their own pace; committed scenario files
  are the drain-completable half. The human may trim list (a) at
  critique time; the lint stays honest either way — untrimmed Tier A
  rows without sets simply remain failing findings until closed.
- R5: `harness-audit`'s evalset-presence check consults
  `evals/COVERAGE.md`: a Tier A gap is a finding, a Tier B row is
  checked against its named tests, a Tier C row is reported as waived
  (one line), and a skill absent from the table is itself the finding.
- R6: `.claude/skills/evals/SKILL.md` + `reference.md` document the
  tier table and the adversarial-scenario naming convention in one
  short section (cite COVERAGE.md, don't restate the table). Mirrors:
  the antigravity evals workflow and the codex evals wrapper
  (`codex/.agents/skills/evals/SKILL.md`, real content per CLAUDE.md)
  receive the equivalent pointer; antigravity harness-audit port ditto;
  `.claude-plugin/plugin.json` `version` bumped; some task's `Touch:`
  lists all of these.

## Out of scope

- CI wiring for `run.sh` — unchanged v1 scope decision.
- Trajectory-assertion depth for existing scenarios —
  `specs/trajectory-evals` (open follow-up tasks 05–07) owns that.
- Evalsets for the Tier C rows — each waiver names its blocker; a
  later spec promotes rows, the table is the place that decision lives.
- LLM-judge grading — graders stay deterministic shell (adopted
  single-call-rubric doctrine applies to workflows, not this harness).

## Acceptance criteria

- [ ] `bash evals/lint-eval-coverage.sh` exits 0 on the completed tree
      (R1, R2, R4 — L2: the policy is enforced by executing it, not by
      grepping for prose; phrase `lint-eval-coverage` absent today,
      verified 2026-07-19).
- [ ] `bash tests/test_eval_coverage_lint.sh` exits 0, and it contains
      a failing-fixture case per R2 violation class (R3 — L2:
      exercises the lint's own failure behavior).
- [ ] `grep -c 'COVERAGE.md' .claude/skills/harness-audit/SKILL.md` ≥ 1
      and `grep -c 'COVERAGE'
antigravity/.agents/skills/harness-audit/SKILL.md` ≥ 1 (R5 + its
      CLAUDE.md same-commit mirror; both literals absent from both
      files today, verified 2026-07-19). Depth ceiling:
      prose checklist edit — the scenario-count/adversarial structure
      itself is enforced behaviorally by criterion 1's lint run, which
      is why no separate `ls` criterion exists; behavioral complement
      for the tier-aware wording is a manual-pending human read at
      review.
- [ ] `grep -c 'COVERAGE.md' .claude/skills/evals/SKILL.md` ≥ 1 and
      `grep -c 'COVERAGE.md' codex/.agents/skills/evals/SKILL.md` ≥ 1
      and `grep -c 'COVERAGE' antigravity/.agents/workflows/evals.md`
      ≥ 1 (R6; all three literals absent today, verified 2026-07-19);
      closing commit modifies the plugin version line: `git show
<closing-commit> -- .claude-plugin/plugin.json | grep -q
'^+.*"version"'` (R6).

## Open questions

(none — the contested decisions are made in the tier table and R4:
onboard is Tier A with artifact-only assertions, prose-review is
Tier C, the adversarial marker is `NN-adv-*` dir naming, and R4 ships
the full backfill+new list with an explicit trim-at-critique escape.
The table intro invites the human to amend rows; amendments are edits
to COVERAGE.md, not blockers.)

## Parallelization

Task 01 (COVERAGE.md + lint + self-test, TDD) is the foundation. Tasks
02–06 (one new evalset each: prioritize, idea, distill, gate, onboard)
and 07 (the four backfills batched, plus the existence-conditional
critique scenario — batching per this section's earlier note; without
the conditional the critique row never meets the Tier A bar when
`specs/criterion-depth-ladder` has not landed first, and the headline
lint criterion stalls) are disjoint in Touch (each owns only NEW
scenario dirs) and share no undecided design — the `NN-adv-*` marker
and per-skill content contracts are pinned in R4 — so all six run
concurrently. Task 08 (tier-aware harness-audit, evals docs, mirrors,
version bump, and the lint-green headline check) closes, depending on
all of 01–07. Group grammar per specs/drain-rolling-window/SPEC.md's
Parallelization section.

- Group: 02, 03, 04, 05, 06, 07
