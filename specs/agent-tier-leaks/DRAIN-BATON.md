Run-token: 4e18a83a5654fba1
Generation: 2
Spec: specs/agent-tier-leaks

## Done / next
- 01-verifier-leak-trace: DONE, merged (outcome (a): docs/memory/verifier-tier-leak.md — leak = plugin cache 0.6.2 model:inherit; verifier.md NOT edited)
- 02-namespace-attribution: DONE, merged (hypothesis confirmed in agentprof README; NO shadow copies found anywhere)
- Next: 03-closing-gate (deps 01,02 done) — expected verified NO-OP: no .claude/agents/*.md edits this spec, no shadow copies flagged; record the no-op evidence per its acceptance. Tasks 04, 05 are draft stubs — never dispatch.
- Spec close note: R2 acceptance (verify-only) is already satisfiable — drain-wake-cost task 02 merged.

## Anomalies
- One hub owns all three agentprof specs (single Run-token across the three DRAIN-OWNER.md files) — gen 2 drains all three.
- The three remaining tasks share `.claude-plugin/plugin.json` in Touch, so they are NOT groupable: run SEQUENTIALLY, deterministic order tl/03 -> dw/03 -> audit/02.
- Gen-1 group A ran 5 concurrent workers, all DONE first attempt; no parked tasks, no rescues, no deferred questions.
- Repo has no scripts/check.sh; gates used: bash evals/lint-ultra-gate.sh + per-task acceptance greps (+ claude plugin validate . where plugin.json changes).
- NOTE: merged task 01-drain-skill-text changed drain SKILL.md's own baton rule to max(2,6-W); this run was launched from plugin 0.8.13 (4-verdict rule) — gen 2 launched headless from the same plugin text.
