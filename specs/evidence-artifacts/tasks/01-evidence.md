# Task 01: Caller-directed evidence files from the verifier

Status: done
Depends on: ../../hardening-quick-wins/tasks/03-task-budgets.md (drain reference.md overlap; cross-spec waves in ../SPEC.md)
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

<!-- Plan (/build):
1. .claude/agents/verifier.md — add Write to tools:; new "Evidence file"
   body section: caller-provided path → write full report (verdict,
   per-criterion command + output tail ~10 lines, gates, scope creep),
   create parent dirs, re-verify overwrites (latest verdict wins, stale
   PASS must not survive a FAIL); no path → write nothing, never derive.
   Chat message keeps under-a-page format + ends with pointer to path.
2. .claude/skills/build/SKILL.md — step 3.3: derive evidence path
   (specs/<slug>/tasks/<name>.md → specs/<slug>/evidence/<name>.md; bare
   specs/<slug>/SPEC.md → evidence/spec.md; other layouts → no path) and
   pass it; close-out: commit evidence file with code + task file,
   task-file evidence lines cite it; other-layout case noted at close-out.
3. .claude/skills/drain/SKILL.md — DONE bullet: merge carries the
   evidence/ file. drain/reference.md — headless fallback: one line,
   orchestrator pastes post-merge re-run into
   specs/<slug>/evidence/<name>.md before flipping to done.
4. Antigravity mirrors: verifier skill (same rule + file/message split,
   walkthrough complements not replaces), build workflow (derive + pass
   path, commit file, walkthrough note), drain workflow (DONE clause).
Risks: regression guards in drain/reference.md ("data, not instructions"
x2, "over budget" x2) must survive; no plugin.json bump (out of scope per
spec); spawned verifier runs OLD definition — verify new text by greps
and reading, not by its behavior.
-->

## Acceptance

- [x] `grep -q "tools:.*Write" .claude/agents/verifier.md && grep -qi "when the caller provides" .claude/agents/verifier.md` → pass — verifier: exit 0 (../evidence/01-evidence.md)
- [x] `grep -qi "output tail" .claude/agents/verifier.md && grep -qi "overwrit" .claude/agents/verifier.md` → pass — verifier: exit 0 (../evidence/01-evidence.md)
- [x] `grep -q "evidence/" .claude/skills/build/SKILL.md` → pass — verifier: exit 0 (../evidence/01-evidence.md)
- [x] `grep -q "evidence/" .claude/skills/drain/SKILL.md && grep -q "evidence/" .claude/skills/drain/reference.md` → pass — verifier: exit 0 (../evidence/01-evidence.md)
- [x] `grep -q "evidence/" antigravity/.agents/skills/verifier/SKILL.md && grep -q "evidence/" antigravity/.agents/workflows/build.md && grep -q "evidence/" antigravity/.agents/workflows/drain.md` → pass — verifier: exit 0 (../evidence/01-evidence.md)
- [x] Regression guards (earlier waves' phrases survive this task's edits): `test "$(grep -c 'data, not instructions' .claude/skills/drain/reference.md)" -ge 2 && test "$(grep -c 'over budget' .claude/skills/drain/reference.md)" -ge 2` → pass — verifier: exit 0 (../evidence/01-evidence.md)
