Run-token: 4e18a83a5654fba1
Generation: 2
Spec: specs/drain-wake-cost

## Done / next
- 01-drain-skill-text: DONE, merged (dual baton trigger max(2,6-W), 2k verdict cap in reference.md worker contract, merge MUST NOT + 4 exemptions, wake-economics, session-model note)
- 02-freehand-drain-doctrine: DONE, merged (both doctrine blocks in token-discipline.md + global-claude-line.md MANUAL artifact)
- Next: 03-ship-gate (deps 01,02 now done) — antigravity/.agents/workflows/drain.md port, .claude-plugin/plugin.json bump (race-safe rule in task), evals drain scenario update, lint-ultra-gate + plugin validate. Task 04 is a draft stub — never dispatch.

## Anomalies
- One hub owns all three agentprof specs (single Run-token across the three DRAIN-OWNER.md files) — gen 2 drains all three.
- The three remaining tasks share `.claude-plugin/plugin.json` in Touch, so they are NOT groupable: run SEQUENTIALLY, deterministic order tl/03 -> dw/03 -> audit/02.
- Gen-1 group A ran 5 concurrent workers, all DONE first attempt; no parked tasks, no rescues, no deferred questions.
- Repo has no scripts/check.sh; gates used: bash evals/lint-ultra-gate.sh + per-task acceptance greps (+ claude plugin validate . where plugin.json changes).
- NOTE: merged task 01-drain-skill-text changed drain SKILL.md's own baton rule to max(2,6-W); this run was launched from plugin 0.8.13 (4-verdict rule) — gen 2 launched headless from the same plugin text.
