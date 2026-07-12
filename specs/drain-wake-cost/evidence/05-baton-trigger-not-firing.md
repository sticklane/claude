# Verification: Task 05 — baton trigger not firing

Verdict: PASS

## Criterion 1 — EVIDENCE.md "Task 05 findings" section
Command: `git diff 25e9cc1954e19a1ed3a0ab4ccb8515020f27267a -- specs/drain-wake-cost/EVIDENCE.md`
Result: PASS. New "## Task 05 findings (2026-07-12): the 3a check is skipped,
not too loose" section added. States hypothesis 2b confirmed for `55ae834e`
("hypothesis (2b) confirmed, cleanly" — 9 verdicts over 6+ hours, baton-pass
marker never emitted). Separately analyzes `80161f1c` (successor-wake latency,
not the 3a trigger) and `c2cec1dd` (reprimes occurred after the drain turn
ended — not a baton-trigger failure). Each has session-id + concrete
quote/paraphrase citations (transcript line counts, timestamps, final-message
quote, grep-vs-actual-emission methodology). Explicitly states "No change to
the `max(2, 6 − W)` formula itself (2a was not supported by the transcript
evidence)."

## Criterion 2 — SKILL.md/reference.md diff reflects fix, 3a section coherent
Command: `git diff 25e9cc1954e19a1ed3a0ab4ccb8515020f27267a -- .claude/skills/drain/SKILL.md`
Result: PASS. Step 3's closing text now reads "Every recorded verdict ends
here, not at step 2: ... evaluate 3a's relaunch trigger below. Looping back
to step 2 without that check first is a process violation... Only after 3a
clears — trigger not met, or fired and this generation's turn has ended —
does the hub loop to step 2." Step 3a's opening now reads "you enter it
after EVERY recorded verdict (step 3's closing line sends you here
unconditionally) or 3b auto-breakdown attempt, never only when it happens to
feel like a good moment." Read together, these two passages state one
consistent rule (mandatory evaluation of 3a after every verdict, no loop
back to step 2 without it) with no contradictory trigger text. No change to
reference.md (EVIDENCE.md states its derivation text was accurate and
unaffected — consistent with the empty reference.md diff observed).

## Criterion 3 — lint-ultra-gate
Command: `bash evals/lint-ultra-gate.sh`
Output: `lint-ultra-gate: OK — all ultra mentions gated in 4 files`, exit 0. PASS.

## Criterion 4 — Touch scope
Command: `git diff 25e9cc1954e19a1ed3a0ab4ccb8515020f27267a --stat`
Output:
```
 .claude/skills/drain/SKILL.md                      | 19 ++++--
 specs/drain-wake-cost/EVIDENCE.md                  | 76 ++++++++++++++++++++++
 .../tasks/05-baton-trigger-not-firing.md           |  2 +-
 3 files changed, 90 insertions(+), 7 deletions(-)
```
Result: PASS. Only the two Touch-listed files (SKILL.md, EVIDENCE.md) plus
the task's own file changed. The task-file diff is a single-line Status flip
(`pending` → `in-progress`), the append-only edit workers are always
permitted on their own task file — not scope creep. `reference.md` untouched
(consistent with "no change needed" claim). An untracked `slack-relay/`
directory appears in `git status` but is unrelated pre-existing untracked
material, not part of this diff (git diff --stat doesn't include it).

## Criterion 5 — Sanity-check EVIDENCE.md claim against actual SKILL.md diff
Result: PASS. EVIDENCE.md's "Fix shipped" paragraph quotes the exact new
text — "before doing anything else... evaluate 3a's relaunch trigger below.
Looping back to step 2 without that check first is a process violation, not
a discretionary skip" and step 3a's "after EVERY recorded verdict (step 3's
closing line sends you here unconditionally)... never only when it happens
to feel like a good moment" — both strings are verbatim present in the
actual SKILL.md diff. The described fix (forcing evaluation of 3a before
looping to step 2) matches what's actually in the file.

## Append-only task-file check
Command: `git diff 25e9cc1954e19a1ed3a0ab4ccb8515020f27267a -- specs/drain-wake-cost/tasks/05-baton-trigger-not-firing.md`
Only change: `Status: pending` → `Status: in-progress`. No acceptance
checkboxes ticked, no evidence-citation lines added inline in the task file
(citations live in EVIDENCE.md instead, which satisfies criterion 1's
"quote/paraphrase citations" requirement there). Goal/Steps/Touch/Budget/
acceptance-criterion text unchanged. Compliant with the append-only rule.

## Observation (not a scope violation, flagged for the record)
Status is left at `in-progress` and no acceptance checkboxes are ticked in
the task file, even though the underlying artifacts (EVIDENCE.md section,
SKILL.md fix, passing lint gate) satisfy criteria 1–3 and 5. The 4th
criterion (MANUAL, deferred — a week-later agentprof re-check) is correctly
left unchecked per its own text. Criteria 1–3 could have been ticked but
were not; this doesn't fail verification (the caller's instructions define
the checks by content, not by checkbox state) but is worth noting for
whoever finalizes the task's Status.

## Gates
No repo-wide `scripts/check.sh` run requested by the caller's criteria;
`evals/lint-ultra-gate.sh` is the specific gate named and it passed.

## Overall verdict: PASS
