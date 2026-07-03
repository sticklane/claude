# Task 01: Caller-directed evidence files from the verifier

Status: pending
Depends on: none (within this spec; see cross-spec ordering in
../SPEC.md Parallelization)
Budget: 40 turns
Spec: ../SPEC.md (requirements R1–R6)

## Goal

The verifier agent gains `Write` and persists its full report only to a
caller-provided evidence path; /build derives that path
(`specs/<slug>/…` layouts only) and commits the file; drain's docs state
which merges carry evidence (background: yes, headless: orchestrator
pastes the post-merge re-run); antigravity mirrors updated.

## Touch

- `.claude/agents/verifier.md`
- `.claude/skills/build/SKILL.md` (step 3 + close-out)
- `.claude/skills/drain/SKILL.md` (one clause)
- `.claude/skills/drain/reference.md` (one headless line)
- `antigravity/.agents/skills/verifier/SKILL.md`
- `antigravity/.agents/workflows/build.md`
- `antigravity/.agents/workflows/drain.md` (one clause)

## Steps

1. verifier.md: add `Write` to `tools:`; body gains the
   caller-provided-path rule (write full report — verdict, per-criterion
   command + output tail, gates, scope creep — creating dirs; no path →
   write nothing, never derive one; re-verify overwrites). The chat
   message keeps the under-a-page format and ends with a pointer to the
   evidence path.
2. build SKILL.md step 3: pass the derived evidence path
   (`specs/<slug>/tasks/<name>.md` → `specs/<slug>/evidence/<name>.md`;
   bare `specs/<slug>/SPEC.md` → `evidence/spec.md`; other layouts → no
   path, close-out notes non-persistence). Close-out: commit the
   evidence file; task-file evidence lines cite it.
3. drain SKILL.md: one clause — background DONE merges carry the
   `evidence/` file. drain reference.md headless fallback: one line —
   no verifier ran, orchestrator pastes its post-merge acceptance re-run
   into `specs/<slug>/evidence/<name>.md` before flipping to done.
4. Mirrors: antigravity verifier skill (same rule + file/message split),
   build workflow (pass path + commit + walkthrough note), drain
   workflow (background clause).

## Acceptance

- [ ] `grep -q "tools:.*Write" .claude/agents/verifier.md && grep -qi "when the caller provides" .claude/agents/verifier.md` → pass
- [ ] `grep -qi "output tail" .claude/agents/verifier.md && grep -qi "overwrit" .claude/agents/verifier.md` → pass
- [ ] `grep -q "evidence/" .claude/skills/build/SKILL.md` → pass
- [ ] `grep -q "evidence/" .claude/skills/drain/SKILL.md && grep -q "evidence/" .claude/skills/drain/reference.md` → pass
- [ ] `grep -q "evidence/" antigravity/.agents/skills/verifier/SKILL.md && grep -q "evidence/" antigravity/.agents/workflows/build.md && grep -q "evidence/" antigravity/.agents/workflows/drain.md` → pass
