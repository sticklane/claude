# Pre-commit review: one bounded bug-hunt in build's close-out, findings fixed in-Touch

## Problem

Every /build close-out — attended or as a drained/autopilot worker — runs
a fresh-eyes verifier (acceptance-focused) and a simplification pass
before the final commit, but no bug-hunting review of the diff ever
fires: the verifier checks the task's acceptance criteria, not
regressions outside them, and /simplify is explicitly quality-only. In
the drained path this means unreviewed code merges to main unattended.
The toolkit's doctrine already bounds what a sane review step looks like
(token-discipline.md ≈47: bound evaluator-optimizer loops, skip model
review where a deterministic check decides; anthropic-playbook.md ≈79:
"a reviewer prompted to find gaps always finds some — fix what changes
behavior, don't chase everything") — it just was never wired in.

## Solution

One new step in `.claude/skills/build/SKILL.md`'s close-out, positioned
AFTER the simplification pass + acceptance re-run and BEFORE the final
commit (today ≈lines 72–88). Single pass, never looped. Model judgment
is confined to the review itself; everything around it is rules:

- **Deterministic skip gate (rules, not model).** Compute the task's
  full diff with ONE command against the session base build's step 0
  already records (`git rev-parse HEAD` at task start — the same base
  the verifier uses; NOT `merge-base <default-branch>`, which collapses
  to HEAD for attended builds working directly on the default branch
  and would exclude mid-stream commits): `git add -A && git diff <step0-base>
  --numstat` — staging first is what makes brand-NEW files (untracked
  implementation the close-out hasn't committed yet) visible to the
  diff; with everything staged the command covers committed, staged,
  and new work exactly once. (Staging here is harmless: the final
  commit follows this step.) Classify paths:
  NON-product = matching `docs/**`, `**/*.md`, `tests/**`, `test/**`,
  `**/test_*`, `**/*_test.*`, `**/*.test.*`, `**/*.spec.*`,
  `**/*.json`, `**/*.yaml`, `**/*.yml`, `**/*.toml`, `**/*.lock`.
  SKIP the review when there are no product paths (docs/config/
  tests-only diff) or when total added+deleted lines across product
  paths < 25. A skipped review records its reason and close-out
  proceeds straight to commit.
- **The review (model, low tier).** Invoke the harness `/code-review`
  via the Skill tool when available, passing `low` as the skill's
  args (its effort-level argument: low/medium = fewer, high-confidence
  findings); if the runtime's Skill tool cannot pass args, invoke it
  bare — the fix policy below still bounds what gets acted on. Where unavailable (worker contexts
  without the plugin), fall back to ONE subagent on the diff — same
  "if available, otherwise apply its principles" pattern the
  simplification pass already uses — prompted for high-confidence
  correctness/behavior findings only, return capped ≤1k tokens. Run it
  inline or read its output directly; never block on a background
  notification (drain reference.md's sub-reviewer clause, cited not
  restated).
- **Fix policy (rules).** For each finding: fix immediately iff it is a
  correctness/behavior defect AND the fix stays inside the task's
  `Touch:` list — or, when no `Touch:` header exists (attended builds
  from a bare SPEC.md, tasks authored pre-Touch), inside the files
  touched this session, the same scope the simplification pass already
  uses; after any fixes, re-run the task's acceptance commands
  (and the simplification-pass acceptance re-run's standard gates).
  Findings needing out-of-Touch edits, or judged uncertain, are never
  fixed inline: attended, surface them to the user; unattended, they go
  in the worker's `Discovered:` section (drain drafts them). Style/
  simplification findings are dropped — that pass already ran. NO second
  review after fixes (the bound: one review, one fix cycle).
- **Record.** One line in the task's evidence (worker report / evidence
  file): `review: N findings, M fixed, K discovered` or
  `review skipped: <docs-only|tests-only|tiny-diff (<lines>)>`.

Drained/autopilot workers inherit the step automatically — they execute
build's SKILL.md; the existing no-block-on-sub-reviewer worker-prompt
clause already covers the fallback subagent. /critique is untouched: it
stays the design-level (spec/plan) adversary; this step is the
working-diff bug hunt its description already routes elsewhere. Skill
changes require the antigravity mirror + plugin bump, and build is
ultra-gated (`evals/lint-ultra-gate.sh` must stay green).

## Requirements

- R1: build's close-out contains the review step after the
  simplification pass and before the final commit, explicitly bounded:
  the words "one pass" (or equivalent single-pass language) appear, and
  no re-review after fixes is permitted by the text.
- R2: the skip gate is pinned in build's SKILL.md as the exact single
  numstat command against the step-0 recorded base plus the NON-product
  pattern list above and the <25 product-line threshold; the step's
  first action is the skip computation, and a skip short-circuits to
  commit with the recorded reason.
- R3: reviewer selection is pinned: `/code-review` via the Skill tool
  with args `low` when available (bare invocation when args cannot be
  passed); otherwise ONE fallback subagent whose
  prompt (in build's SKILL.md) demands high-confidence
  correctness/behavior findings only and caps the return at ≤1k tokens;
  the text forbids blocking on a background sub-reviewer notification,
  citing drain's existing clause.
- R4: the fix policy is pinned: fix only correctness/behavior findings
  whose edits stay inside the task's `Touch:` — with the no-Touch
  fallback pinned to files touched this session (the simplification
  pass's scope); re-run acceptance
  commands after fixes; out-of-Touch or uncertain findings → user
  (attended) / `Discovered:` (unattended); style findings dropped.
- R5: the outcome line format is pinned
  (`review: N findings, M fixed, K discovered` /
  `review skipped: <reason>`) and lands in the evidence the close-out
  already writes.
- R6: `tests/test_review_skip.sh` (model-free) builds a throwaway repo
  with a recorded step-0 base, MID-STREAM COMMITS, staged and unstaged
  edits, and asserts the documented single-command gate end to end
  (base selection + numstat + classifier + threshold): docs-only →
  skip, tests-only → skip (including `.test.ts`/`.spec.ts` names),
  24 product lines → skip, 26 product lines → review, mixed
  docs+26-product → review, an UNTRACKED new 26-line product file →
  review (the git-add-first clause), and committed-then-modified lines
  counted exactly once. Rides the existing `for t in tests/test_*.sh` gate.
- R7: the antigravity mirror for build is the WORKFLOW port
  `antigravity/.agents/workflows/build.md` (build is human-only;
  CLAUDE.md: "human-only skills→workflows" — there is NO
  antigravity/.agents/skills/build/), updated in the same commit to
  carry the new step (workflow and skill are not byte-identical;
  mirror the step's content in the workflow's shape);
  `.claude-plugin/plugin.json` bumped once;
  `bash evals/lint-ultra-gate.sh` stays green.

## Out of scope

- Orchestrator-side pre-merge review in drain (rejected in interview:
  findings would arrive after the worker is gone, forcing re-dispatch
  instead of in-context fixes).
- Any change to /critique (design-level adversary) or to the verifier.
- Model review in hooks — the gate stays deterministic by design.
- A review loop (review → fix → re-review): explicitly bounded to one
  pass by doctrine.
- High-effort review tiers or multi-reviewer panels for routine commits.
- Reviewing docs-only, tests-only, or tiny diffs (the skip gate exists
  precisely to not spend here).
- Retrofitting review into autopilot/drain text beyond what they inherit
  from build's procedure.

## Acceptance criteria

- [ ] `bash tests/test_review_skip.sh` → exit 0 (R6; seven fixture
      cases named in output)
- [ ] `grep -c "code-review" .claude/skills/build/SKILL.md` → ≥ 1 and
      `grep -ci "one pass" .claude/skills/build/SKILL.md` → ≥ 1 (R1, R3)
- [ ] `grep -c "numstat" .claude/skills/build/SKILL.md` → ≥ 1 and
      `grep -c "review skipped" .claude/skills/build/SKILL.md` → ≥ 1 (R2, R5)
- [ ] R4's in-Touch fix bound present:
      `grep -c "inside the task's \`Touch:\`" .claude/skills/build/SKILL.md` → ≥ 1
      (or an equivalent literal the implementer records in evidence),
      plus `grep -c "touched this session" .claude/skills/build/SKILL.md` → ≥ 2
      (simplification pass + the review step's no-Touch fallback)
- [ ] `grep -qE "review: N findings|review:.*fixed.*discovered" .claude/skills/build/SKILL.md` → exit 0 (R5 format pinned; -E for BSD-grep portability)
- [ ] `for tok in code-review numstat "review skipped"; do grep -qc "$tok" antigravity/.agents/workflows/build.md || exit 1; done` → exit 0 (workflow mirror carries the step), and `git diff <base>..HEAD -- .claude-plugin/plugin.json | grep -c '"version"'` → 2 (R7)
- [ ] `bash evals/lint-ultra-gate.sh` → exit 0 (R7)
- [ ] Full gate suite green: `for t in tests/test_*.sh; do bash "$t"; done`,
      `./bin/check-agent-model-pins`, `./evals/runner-selftest.sh`,
      `./specs/status.sh`, `claude plugin validate .`
- [ ] MANUAL-PENDING (human-run; /build is disable-model-invocation so
      no unattended worker can execute this; per
      docs/memory/unattended-worker-tool-limits.md): the next attended
      /build (or drained queue) of a task with a ≥25-line product diff
      shows the `review: …` line in its evidence file, and a docs-only
      task shows `review skipped: docs-only`; paste both lines into
      `specs/precommit-review/evidence/`

## Open questions

(none)
