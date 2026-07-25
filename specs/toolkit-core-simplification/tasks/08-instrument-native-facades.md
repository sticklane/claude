# Task 08: instrument the native work, build, and drain façades

<!-- Task state is canonical in bd. The Status line is frozen display and is not edited by workers. -->

Status: pending
Depends on: 03, 04, 05, 07
Priority: P1
Budget: 44 turns
Spec: ../SPEC.md (requirements R5, R8)
Touch: .claude/skills/work/SKILL.md, .claude/skills/build/SKILL.md, .claude/skills/drain/SKILL.md, .claude/skills/drain/reference.md, .claude/skills/drain/dispatch-worker.sh, .claude/agents/implementation-worker.md, .claude/agents/verifier.md, .claude/agents/critic.md, runtimes/claude-code.md, runtimes/codex.md, runtimes/antigravity.md, tests/test_agentic_facade_conformance.sh, tests/test_codex_skill_entrypoints.sh, tests/inventory/08-facades.json, specs/toolkit-core-simplification/surface-inventory/08-facades.json

## Goal

Make each façade emit the shared protocol events at its existing native
boundaries while retaining its intent, permissions, isolation, and agent
manager. Codex must use the Codex ultracode-equivalent collaboration shape
everywhere Ultra orchestration is called for; Antigravity must use native
subagents; Claude must retain Workflow.

## Touch

Do not add a composer, common loop, scheduling helper, or nested verifier.
Workers run acceptance and targeted tests; the native orchestrator owns one
verifier/critic barrier and one final canonical gate.

## Steps

1. Write failing façade/runtime fixtures that normalize the emitted traces.
2. Instrument `/work`, `/build`, and `/drain` claim, session-link, worker,
   review, gate, close, and cleanup boundaries using the event CLI.
3. Align all three runtime profiles and compact prompts with the contract,
   including denied-path and interruption behavior. Every record-producing
   worker/reviewer contract carries the run ID; supported headless dispatch
   exports `AGENTIC_RUN_ID`.

## Acceptance

- [ ] `bash tests/test_agentic_facade_conformance.sh work build drain` → every façade/runtime pair produces a valid equivalent trace with claim-time UUIDv7 creation, bd comment, environment or compact-prompt propagation, run ID on every verdict/review/gate record, retry identity reuse, linked reopen identity, one gate, and complete cleanup (L2).
  Depth ceiling: deterministic fixtures cannot invoke all three proprietary native agent managers hermetically — behavioral complement is a manual-pending three-runtime `evals/run.sh drain` journey with `.claude/runtime.md` set in turn to `claude-code`, `codex`, and `antigravity`, recorded in `REPORT.json`.
- [ ] `bash tests/test_codex_skill_entrypoints.sh` → Codex discovery and native collaboration contracts remain live (L2).
- [ ] `bash scripts/check.sh` → the instrumented native façades pass the full inventoried suite (L3).
