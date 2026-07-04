# Verification evidence: Task 01 — Majority-PASS verifier votes

Verdict: PASS
Verified: 2026-07-03, branch task/01-majority-votes (working tree, 3 uncommitted
modified files), commit base 7bd93e3. Verifier: independent (did not write this code).

## Runnable acceptance commands (run from repo root)

All commands executed exactly as written in the task file; recorded exit status
is from a fresh run in this verification session.

1. R1 phrases — exit 0 ✓
   ```
   grep -q "majority PASS" .claude/skills/drain/reference.md && grep -q "three independent verifier" .claude/skills/drain/reference.md
   ```
   Filter paragraph now reads "three independent verifier runs" and "survives
   only on majority PASS (two of three)".

2. R2 rank paragraph — exit 0 ✓
   ```
   sed -n '/^\*\*Rank\./,/^$/p' .claude/skills/drain/reference.md | grep -q "PASS votes" && grep -q "Drain, not the verifier" .claude/skills/drain/reference.md && sed -n '/^\*\*Rank\./,/^$/p' .claude/skills/drain/reference.md | grep -q "t1 before t2"
   ```
   Scoped to the Rank paragraph itself: "most PASS votes first (3 ahead of 2)",
   "(t1 before t2 before t3)", and "Drain, not the verifier ... mechanically"
   retained. Key order verified in the prose: PASS votes → summed gate findings
   ("summed across the candidate's three verifier reports") → smallest
   `git diff --stat` total → lowest angle index (explicitly "the final
   tiebreak, so the mechanical ranker always terminates with an order").
   "No new verifier output mode" retained.

3. R1 negative (old single-run sentence gone) — exit 0 ✓
   ```
   ! grep -qi "one verifier run per candidate" .claude/skills/drain/reference.md
   ```
   Also cross-checked: `grep -rn "one verifier" .claude/skills/drain/ antigravity/.agents/workflows/drain.md`
   returns no stale single-run text.

4. R3 cost sentence scoped to Tournament section — exit 0 ✓
   ```
   sed -n '/^## Tournament/,/^## /p' .claude/skills/drain/reference.md | grep -qi "human-gates"
   ```
   Sentence at reference.md:132, inside `## Tournament` (section spans lines
   122–199): "Verifier votes triple verifier cost inside tournaments only —
   bounded by the at-most-one-tournament-per-task rule — and the tournament
   remains inside the human-authorized /drain launch (docs/human-gates.md)."
   One sentence; cites docs/human-gates.md without restating it.

5. R4 mirror — exit 0 ✓
   ```
   grep -q "majority PASS" antigravity/.agents/workflows/drain.md && grep -q "PASS votes" antigravity/.agents/workflows/drain.md && ! grep -qi "one verifier-skill run per candidate" antigravity/.agents/workflows/drain.md
   ```
   Diff inspection confirms the mirror adopts the FULL semantics, not just the
   marker phrases: three independent verifier-skill runs, fresh eyes per run,
   no evidence path, majority PASS (two of three), FAIL/INCOMPLETE as non-PASS
   votes, verifier-BLOCKED disqualifies outright with quoted content recorded,
   worker-BLOCKED/DEFERRED handling unchanged, rank keys PASS votes → summed
   gate findings → diff stat → angle index. Old single-run Filter/Rank lines
   replaced in place (visible as removals in the diff), not appended-around.

6. R6 research record — exit 0 ✓
   ```
   grep -q "N-vote" docs/external-playbooks.md
   ```
   Follow-on line appended directly to the AlphaCode 2 entry: "N-vote
   adjudication — multiple independent verifier votes with majority rule — is
   the standard cure for single-judge error in generate–filter–rank pipelines
   (harness-observed Workflow quality pattern: adversarial verify votes;
   adopted here for the tournament filter). Harness-observed; no public URL."

## Manual paper dry-run (spec end-to-end criterion)

Read the rewritten Filter/Rank prose in both .claude/skills/drain/reference.md
and antigravity/.agents/workflows/drain.md; each scenario is decided
unambiguously by the prose:

- 3/2/1 PASS votes: "survives only on majority PASS (two of three)" — the
  1-PASS candidate is filtered (1 < 2); 3-PASS and 2-PASS survive. Rank's
  first key "most PASS votes first (3 ahead of 2)" places the 3-PASS candidate
  ahead of the 2-PASS one regardless of gate-finding counts (gate findings are
  the second key). ✓
- 2-2 vote tie: first key ties, prose falls through to "fewest gate findings
  summed across the candidate's three verifier reports". ✓
- Full tie on all three keys: "then — the final tiebreak, so the mechanical
  ranker always terminates with an order — lowest angle index (t1 before t2
  before t3)" → t1 first. ✓
- 2 PASS + 1 BLOCKED: "A verifier run returning BLOCKED ... is NOT a vote: it
  DISQUALIFIES the candidate outright regardless of the other votes, and the
  verifier's quoted content goes into the recorded evidence — ... two PASS
  votes never drop the quote." → DISQUALIFIED, quote recorded, explicitly not
  droppable by two PASS votes. Mirror carries the same rule. ✓

## Standard gates

- No test suite / lint applies to prose-only skill edits. The repo's
  "Testing changes" gate (/evals via evals/run.sh) applies only to skills
  with a stored evalset; `evals/` contains only `breakdown` — no drain
  evalset exists, so no eval gate to run.

## Scope check

- `git status` shows exactly the three Touch-listed files modified:
  .claude/skills/drain/reference.md, antigravity/.agents/workflows/drain.md,
  docs/external-playbooks.md. No other changes.
- plugin.json untouched — correct: the task file scopes OUT R5 (rf-99 owns the
  bump). Note: CLAUDE.md's convention says to bump plugin.json whenever skill
  behavior changes; the binding Touch list overrides it here, and rf-99 must
  actually deliver that bump for spec R5 to be satisfied overall.
- Diff shows no removed semantics beyond the replaced single-run sentences;
  Generate, Merge, slot-machine, and verdict routing untouched (spec's
  out-of-scope list respected).
- No overfitting: marker phrases appear inside full semantic rewrites, not as
  isolated grep-bait; the negative greps confirm the old sentences were
  replaced, not appended-around.
