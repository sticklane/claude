# Critique findings — trajectory-evals (NOT READY)

Recorded by drain critique intake, gen 6, Run-token e83f34f07094a4fa, 2026-07-12.
Critic verdict: **NOT READY**. Fix these, then re-run /critique to earn `Breakdown-ready: true`.

## 1. [conf 90] Codex mirror obligation missing — will silently ship un-mirrored + self-contradictory
R5 (SPEC.md:59-67) and AC (:86-88) name only the antigravity mirror + plugin.json. But
.claude/skills/evals/SKILL.md (edited by R4) is one of the four codex real-content SKILL.md files.
CLAUDE.md: a task whose Touch changes one of .claude/skills/{drain,build,autopilot,evals}/SKILL.md
must also carry codex/.agents/skills/<name>/SKILL.md in Touch. codex/.agents/skills/evals/SKILL.md is
real content (3399 B); line 19 carries "v1 grades artifacts only" and line 41 states the grader
returns "never a transcript" — which the v2 mechanism directly contradicts. No task Touch lists this
path → ships stale + self-contradictory. Fix: add codex/.agents/skills/evals/SKILL.md to R5 + closing
task Touch, with an AC `grep -q "EVAL_TRANSCRIPT" codex/.agents/skills/evals/SKILL.md`.

## 2. [conf 85] R4 AC is `||` where requirement is AND — lets SKILL.md ship stale
AC :85 = `grep -q "EVAL_TRANSCRIPT" .claude/skills/evals/SKILL.md || grep -q ... reference.md`. R4
(:59-62) + Solution (:44-47) require BOTH files to document it, specifically updating the
"v1 grades artifacts only" line at .claude/skills/evals/SKILL.md:11. A worker documenting only
reference.md passes while leaving SKILL.md:11 stale. Fix: split into two &&-joined greps (one per
file), or anchor the SKILL.md grep on the updated line's new phrase.

## 3. [conf 75] plugin.json AC wrong path + no self-verifiable anchor
AC :87-88 "plugin.json version is higher than before" — prose not a runnable command; file is at
.claude-plugin/plugin.json (no top-level plugin.json; current 0.8.48). "higher than before" not
resolvable by a worker lacking the pre-image. Fix: name the real path in R5 Touch; make the AC a
concrete bump target, e.g. `grep -q '"version": "0.8.49"' .claude-plugin/plugin.json`.

## 4. [conf 65] R3 "and passes" clause has no verifiable path off the paid runner
AC :83 (`grep -rl "EVAL_TRANSCRIPT" evals/*/ | grep -q assert.sh`) only proves a scenario references
the transcript; R3 (:56-58) also requires it "passes," shown only by ./evals/run.sh (paid headless,
AC :81). AC :81 is correctly labelled "(paid headless run; human-launched)" = manual-pending, but
R3's pass requirement inherits no such label. Mark the R3 "passes" verification explicitly
manual-pending per docs/memory/unattended-worker-tool-limits.md.

## Non-blocking / verified
Spec does NOT touch any ultra-path skill → no lint-ultra-gate AC required (correctly absent).
`EVAL_TRANSCRIPT` confirmed absent from evals/run.sh today, so AC :80 is not vacuous.

## Triage 2026-07-13 (attended; Steven approved REVISE)

Verdict: REVISE. Edits before re-critique: (1) add codex/.agents/skills/evals/SKILL.md to R5/Touch with its own grep AC (its lines 19 and 41 carry exactly the text this spec would contradict); (2) split the R4 `||` AC into two `&&` greps; (3) fix the plugin.json path, pin the fresh next version (0.8.56+ — the critique's 0.8.49 suggestion is itself stale), and mark R3's "passes" manual-pending. Verified: EVAL_TRANSCRIPT absent from evals/run.sh — problem live.

## Re-critique 2026-07-13 (drain critique intake, run b4adb88f) — still NOT READY, approved plan not yet applied

`git log -- specs/trajectory-evals/SPEC.md` shows no commit since the triage
above — SPEC.md is byte-identical to the state that produced this file's
prior NOT READY verdict. Skipping a redundant full critic dispatch on
unchanged content per token-discipline's "cheap before expensive" — the
three approved triage edits above are the recovery path, unchanged. This
spec's critique intake is spent for this run.
