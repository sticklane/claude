# Evidence: transcript-mined antipatterns, 2026-07-11

Method: two transcript-mining agents over (a) the 07-11 morning drain hub
session (0481d252…) + its 4 largest worker/verifier sidecars, and (b) the
3 largest spec-writer sidecars (session c2cec1dd…) + 4 implementation-
worker sidecars from drain sessions 17545c2e/4a31b7e2/b5b17738/34cfc33e +
c2cec1dd's parallel-dispatch turn. Sidecar files live under
`~/.claude/projects/-Users-sjaconette-claude/<session>/subagents/`.

## Hits (each → one requirement)

- R1 Bash-denial grinding: 87 "don't ask mode" denied-Bash tool_results
  across the morning drain tree (MAIN 16, workers 8/10, verifiers
  30/19/4). Worst single case: verifier a40f8647 cycled ≥9 syntax
  variants of running `evals/lint-ultra-gate.sh` (chained `; echo EXIT`,
  pipes, /tmp copies) through 30 denials before a bare
  `bash evals/lint-ultra-gate.sh` succeeded.
- R2 Sleep-polling loophole: agent a321ed56 chained 23 × `sleep 1` (91s)
  after the harness blocked `sleep 30` with an explicit "don't chain
  shorter sleeps" message; agent aa158790 same pattern (8×+).
- R3 Re-read churn (highest-volume waste by call count in every sampled
  transcript): rod_detect.go read 6× consecutively with zero intervening
  edits (worker a715e206); server.integration.test.ts 5×,
  WishlistPage.tsx 4× (worker a840e970); SPEC.md 25× across critique
  rounds (a04aa9fd); SPEC.md 13× (a321ed56).
- R4 Worktree-path trap: worker a715e206 edited the main-checkout path
  from inside its worktree, got the isolation error, burned a turn;
  another worker (dw03) hit the same error once and self-corrected.
- R5 Scout scope creep: 3 of ~10 scouts in c2cec1dd ran 17/20/21 model
  calls (target 3–10) — failed targeted greps widened to repo-wide
  `grep -r … specs/**.md`, plus duplicate reads inside one scout
  (workboard.py 2×, drain/reference.md 2×).
- R6 Full-file doctrine reads: hub read drain/reference.md whole (1,117
  lines, 71,519 chars); worker dw03 read the antigravity drain port
  whole (862 lines, 57,743 chars) — each needed one section.

## Clean (verified non-problems — no requirement)

- Hub verdict caps held: all 7 Agent results in MAIN 1.3–3.6k chars.
- One verifier and one critic per task; no duplicate verification.
- No tool-output pasting into hub assistant text.
- No formatter fights; no test-suite-per-edit thrashing (1–2 check.sh
  runs per worker).
- Parallel dispatch disjoint by construction (each agent a fresh
  specs/<slug>/ dir, reasoned before dispatch).
- Dead time >60s coincided with awaited child agents, not oversized
  tool-result digestion.
