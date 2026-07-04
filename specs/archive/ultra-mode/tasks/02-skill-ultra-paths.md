# Task 02: `## Ultra path` sections in five skills + gate lint

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
Status: done
Depends on: 01, ../../orchestrator-context/tasks/02-autopilot-parallel-batons.md, ../../workflow-token-efficiency/tasks/01-dispatch-authoring-rule.md
Priority: P1
Budget: 50 turns
Spec: ../SPEC.md (requirements R2–R6, R8, R9-mirror)
Touch: .claude/skills/critique/SKILL.md, .claude/skills/drain/SKILL.md, .claude/skills/parallel/SKILL.md, .claude/skills/build/SKILL.md, .claude/skills/idea/SKILL.md, evals/lint-ultra-gate.sh, CLAUDE.md, antigravity/.agents/skills/critique/SKILL.md, antigravity/.agents/workflows/drain.md, antigravity/.agents/workflows/parallel.md, antigravity/.agents/workflows/build.md, antigravity/.agents/skills/idea/SKILL.md



## Goal

Each of critique, drain, parallel, build, and idea carries a dedicated
`## Ultra path` section (≤ 25 lines each) documenting its ultra variant
per R2–R5, every case-insensitive "ultra" mention within ±3 lines of the
literal marker "active runtime profile" so gate-closed installs read as
today's skills. `evals/lint-ultra-gate.sh` enforces this model-free and
is referenced from CLAUDE.md's testing section. Antigravity mirrors get
the adapted (permanently-closed-gate) text in the same commit.

## Touch

Serialized after orchestrator-context 02 (drain/parallel contention).
Must NOT touch: breakdown or autopilot skills (spec Out of scope —
`grep -rn "ultra"` on them must stay empty), runtimes/claude-code.md
(task 01 owns it), docs/decisions, plugin.json (task 03 bumps).

## Steps

1. Write `evals/lint-ultra-gate.sh` FIRST and confirm it exits non-zero
   on nothing-yet-written or a deliberately marker-less fixture (RED).
2. Add the five `## Ultra path` sections: critique's 3–5 lens-diverse
   panel with dedupe + majority-refute verify and the when-worth-10×
   sentence (R2); drain/parallel's Depends-on-graph-compiled workflow
   dispatch with per-dispatch budget guard and files-remain-the-checkpoint
   rule (R3); build's acceptance-commands-first then 3-verifier
   refute-majority for unrunnable criteria, fix loop bounded at 4 (R4);
   idea's multi-modal sweep + completeness critic for multi-repo ideas
   (R5). All in gated tier-language pointing at the runtime profile.
3. Reference the lint from CLAUDE.md's testing section.
4. Mirror to antigravity with the closed-gate adaptation.
5. Run acceptance.

## Acceptance

- [x] `bash evals/lint-ultra-gate.sh` → exit 0; deleting the marker phrase from one file makes it exit non-zero naming that file (restore after) — verifier: exit 0; deleting marker in parallel/SKILL.md → exit 1 naming `.claude/skills/parallel/SKILL.md:72`/`:75`; restore → exit 0 (evidence/02-skill-ultra-paths.md)
- [x] `grep -rn "ultra" .claude/skills/breakdown/ .claude/skills/autopilot/` → no output — verifier: no output (evidence/02-skill-ultra-paths.md)
- [x] Each `## Ultra path` section (heading to next heading) ≤ 25 lines in all five files — verifier: critique/drain/parallel/build/idea all present, spans ≤17 lines each (evidence/02-skill-ultra-paths.md)
- [x] `grep -q "lint-ultra-gate" CLAUDE.md` → exit 0 — verifier: exit 0 (evidence/02-skill-ultra-paths.md)
- [x] Antigravity mirrors changed in the same commit (`git show --stat` includes antigravity/ paths) — verifier: `git show --stat HEAD` includes all five antigravity mirrors, each adding `## Ultra path` (evidence/02-skill-ultra-paths.md)
- [x] `./evals/run.sh breakdown` still 1/1 (regression; breakdown untouched but shares the queue's eval gate) — `evals/run.sh breakdown` → "1/1 scenarios passed"; verifier confirmed `.claude/skills/breakdown/` unchanged vs base
