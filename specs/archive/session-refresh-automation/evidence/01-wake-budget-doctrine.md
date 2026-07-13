# Verification: 01-wake-budget-doctrine

Verdict: PASS

## Criteria

1. `grep -ci 'wake budget' .claude/rules/token-discipline.md`
   Output: `1` → PASS (≥1)

2. `grep -ci 'refresh-over-carry' .claude/rules/token-discipline.md`
   Output: `1` → PASS (≥1)

3. `grep -c 'session-refresh-automation' .claude/rules/token-discipline.md`
   Output: `2` → PASS (≥1). Confirmed citation not restatement: lines 195 and
   208 read "(specs/session-refresh-automation, which pins the 30-day
   numbers below)" and "Pinned from the 30-day profile
   (specs/session-refresh-automation): 3 is the re-prime median
   deliberately ... and 250k sits between the context p50 and p90" — the
   rule file states only the pinned defaults (3 re-primes, 250k tokens) and
   qualitative rationale; it does NOT restate the actual 30-day figures
   (167 sessions re-primed, p50=3/p90=10/max=23, $1.90 median, $1,838
   total, main-loop context p50=151k/p90=393k) that live in
   specs/session-refresh-automation/SPEC.md:53-56. Citation confirmed, not
   restatement.

4. Manual — "should a watcher loop run on the session model?"
   Subsection's first bullet: "A waiting main loop is a scheduler, not a
   thinker. A main loop that expects to idle past the cache TTL — a
   watch-then-act poller, a self-paced wakeup loop — runs cheap-tier (or
   launchd), dispatching each event's judgment work to an awaited fresh
   subagent; never a frontier-tier main loop that re-warms a fat context
   just to poll." → PASS. Directly answers: no, watcher loops run
   cheap-tier/launchd, not session/frontier-tier.

## Goal check

Subsection "## Session refresh" (lines 190-215 of
.claude/rules/token-discipline.md, 27 lines within the `## Session
refresh` ... `## Cache economics` span — under the ~30-line budget) states
all three R1 points:
- scheduler-not-thinker (bullet 1)
- wake budget / refresh-over-carry (bullet 2, literal term present)
- 3-re-primes-or-250k-context defaults, 30-day evidence cited to
  specs/session-refresh-automation, not restated (bullet 3, verified above)

Drain baton: "The drain-specific verdict-count baton stays owned by
specs/drain-wake-cost (cited, not restated)" — citation present, no
restatement of drain-wake-cost content.

## Touch discipline

Command: `git diff --stat b65ccbec4b03dbb07093975b9698d644cca66198 -- . ':(exclude)specs/session-refresh-automation/tasks/01-wake-budget-doctrine.md'`
Output:
```
 .claude/rules/token-discipline.md | 27 +++++++++++++++++++++++++++
 1 file changed, 27 insertions(+)
```
Only the rule file changed outside the task file itself. PASS.

Task file diff (`git diff b65ccbec4b03dbb07093975b9698d644cca66198 --
specs/session-refresh-automation/tasks/01-wake-budget-doctrine.md`):
append-only — `Status: in-progress` → `Status: done`, four checkboxes
`[ ]` → `[x]`, and each acceptance line gained a trailing evidence
citation (the fourth criterion's original parenthetical instruction "note
the reply in the commit message or ../SPEC.md evidence" was replaced by
the actual recorded evidence text, which is the evidence-citation content
that parenthetical was pointing at — not a rewrite of the criterion
itself, which is unchanged). No edits to Goal, Steps, Touch, Budget, or
criterion command text. PASS.

## Gates / scope creep

No code gates apply (docs-only change to a rules file; no
scripts/check.sh run required for prose). No files outside the Touch list
(.claude/rules/token-discipline.md, the task file) were modified — matches
`git diff --stat` result above.

No overfitting concerns: this is prose doctrine, not code with test
inputs to game.
