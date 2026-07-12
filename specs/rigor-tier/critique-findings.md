# Critique findings — rigor-tier (NOT READY)

Recorded by drain critique intake, gen 6, Run-token e83f34f07094a4fa, 2026-07-12.
Critic verdict: **NOT READY**. Fix these, then re-run /critique to earn `Breakdown-ready: true`.

## 1. [conf 86] Missing `bash evals/lint-ultra-gate.sh` AC — spec edits 3 of 4 ultra-path skills
Spec edits idea/SKILL.md (R2), build/SKILL.md (R4), drain/SKILL.md (R4). CLAUDE.md mandates
`bash evals/lint-ultra-gate.sh` before committing changes to any of the four ultra-path skills.
No AC (SPEC.md:100-107) runs it. Add the gate AC to whichever tasks Touch idea/build/drain SKILL.md.

## 2. [conf 88] Codex mirror obligation for build + drain absent from R8 and Touch
Spec edits .claude/skills/build/SKILL.md and .claude/skills/drain/SKILL.md. CLAUDE.md: a task
whose Touch changes one of the four .claude/skills/{drain,build,autopilot,evals}/SKILL.md files must
also carry the matching codex/.agents/skills/<name>/SKILL.md update in Touch (real content, not
symlinks). Targets exist: codex/.agents/skills/build/SKILL.md, codex/.agents/skills/drain/SKILL.md.
R8 (SPEC.md:84-88) names only antigravity + plugin.json bump. Add both codex paths to a task's Touch
+ an AC anchoring on them.

## 3. [conf 81] R5 list-specs change has an antigravity mirror R8 omits (and R8 path phrasing wrong)
R5 edits .claude/skills/list-specs/SKILL.md. Mirror exists at antigravity/.agents/skills/list-specs/
(under skills/, not workflows/). R8 enumerates only idea/breakdown/build/drain under
antigravity/.agents/workflows/ — list-specs is not in that set. It will silently ship stale. Add
antigravity/.agents/skills/list-specs/SKILL.md to R8 + a task's Touch; correct R8's blanket
"under antigravity/.agents/workflows/" claim.

## 4. [conf 72] R8 AC (SPEC.md:104) vacuous and non-runnable
`grep -rql "Rigor" antigravity/.agents/ | grep -q .` passes if ANY single file contains "Rigor" —
doesn't verify each mirror updated. And "plugin.json version is higher than before" is not runnable:
an unattended worker has no stored baseline. Enumerate specific mirror files with individual grep -q
anchors; replace "higher than before" with a concrete satisfiable bump target
(e.g. `grep -q '"version": "X.Y.Z"'` against the confirmed next version).

## 5. [nit, conf 58] R4 behavioral core has no verifying check
SPEC.md:100-101 grep for literal "Rigor:" in build/drain SKILL.md (absent today, so non-vacuous) but
prove only the string was added, not that gate-scaling behavior was implemented. That behavior is
only exercised by the manual fresh-session test (line 105), which covers R2/idea not R4. Consider a
manual-pending behavioral AC for the prototype build/drain path.

## Anchor-currency check (passed)
`Rigor:` absent from idea/breakdown/build/drain SKILL.md; `rigor` absent from quality-discipline.md;
`prototype` absent from list-specs SKILL.md — all grep-for-new criteria meaningfully non-vacuous today.
No recursive grep over .claude/ (no worktree-sweep risk).
