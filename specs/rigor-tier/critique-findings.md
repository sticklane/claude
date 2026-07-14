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

- an AC anchoring on them.

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

## Triage 2026-07-13 (attended; Steven approved REVISE)

Verdict: REVISE. Edits before re-critique: (1) add the lint-ultra-gate AC to tasks touching idea/build/drain; (2) extend R8 to codex/.agents/skills/{build,drain}/SKILL.md + antigravity/.agents/skills/list-specs/SKILL.md and fix the "workflows/" phrasing; (3) replace the blanket R8 grep with per-file greps and a concrete version pin (plugin.json is 0.8.56 as of triage). Verified: `Rigor:` absent from idea/build/drain/breakdown SKILL.md — problem live.

## Re-critique 2026-07-13 (drain critique intake, run b4adb88f) — still NOT READY, approved plan not yet applied

`git log -- specs/rigor-tier/SPEC.md` shows no commit since the triage
above — SPEC.md is byte-identical to the state that produced this file's
prior NOT READY verdict. Skipping a redundant full critic dispatch on
unchanged content per token-discipline's "cheap before expensive" — the
three approved triage edits above are the recovery path, unchanged. This
spec's critique intake is spent for this run.

## Re-critique 2026-07-13 (post-triage edits applied, commit 87ecafe) — still NOT READY

The three approved triage edits above were applied verbatim (commit
87ecafe: lint-ultra-gate AC added; R8 extended to codex build/drain +
antigravity list-specs mirrors; blanket R8 grep replaced with per-file
greps + a 0.8.58→0.8.59 version pin). Re-running /critique surfaced one
new finding the approved edit list didn't cover:

### 1. [conf 85] R8 still names the wrong antigravity mirror for idea and breakdown

R8 and its AC (SPEC.md ~84-88, ~113) list `antigravity/.agents/workflows/idea.md`
and `antigravity/.agents/workflows/breakdown.md` as the mirrors to update, and
call all four "workflow files under `antigravity/.agents/workflows/`." That's
wrong for idea/breakdown: those `workflows/*.md` files are thin launcher stubs
("Use the idea skill (.agents/skills/idea/SKILL.md) and follow it exactly…");
the real ported content — where R2/R3's behavioral changes actually belong —
lives at `antigravity/.agents/skills/idea/SKILL.md` and
`antigravity/.agents/skills/breakdown/SKILL.md`. build and drain are
different and correctly named: they have no `skills/` copy, their real
content IS directly in `antigravity/.agents/workflows/{build,drain}.md`. This
is the same mirror-path-bucketing bug as prior finding #3 (list-specs); that
one got fixed in the triage round, idea/breakdown did not. Fix: in R8 and its
AC, swap `antigravity/.agents/workflows/{idea,breakdown}.md` for
`antigravity/.agents/skills/{idea,breakdown}/SKILL.md`; narrow R8's blanket
"workflow files under `workflows/`" phrasing to build/drain only. Confirmed
non-vacuous: `rigor` absent (count 0) today from both real skill-mirror
targets.

### 2. [conf 60, spec-range, repeat of prior nit #5] R4 still has no verifying check

Unaddressed — not part of the approved triage list, carried forward for the
next round.

### Verified clean this round

Version pin (0.8.58→0.8.59) accurate; all per-file grep ACs in the applied
edits are non-vacuous against current repo state; `bash evals/lint-ultra-gate.sh`
exists and exits 0 today; all codex/antigravity target paths referenced in
the applied R8 exist.

Not yet triaged for approval — the idea/breakdown mirror-path fix (finding 1
above) needs the same attended-approval step the prior round got before
another edit lands.

## Triage 2026-07-13/14 (attended; Steven approved fix for finding 1)

Verdict: fix applied. R8's prose and AC swapped
`antigravity/.agents/workflows/{idea,breakdown}.md` for
`antigravity/.agents/skills/{idea,breakdown}/SKILL.md`, and R8's blanket
"workflow files under `workflows/`" phrasing narrowed to build/drain only.
Finding 2 (R4 has no verifying check, conf 60, spec-range nit) remains
unaddressed and not part of this approval — carried forward for the next
round. Re-run `/critique` to check whether this earns `Breakdown-ready: true`.
