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

## Re-critique 2026-07-14 (drain critique intake, gen 3, run c92aedb1ae49f8d3) — still NOT READY

Finding 1's fix (idea/breakdown mirror paths) verified correct and accurate
against the live tree: `antigravity/.agents/workflows/{idea,breakdown}.md`
confirmed as thin 5/19-line launcher stubs, real content at
`antigravity/.agents/skills/{idea,breakdown}/SKILL.md`, R8 + AC now name
those correctly. But a new, higher-severity blocker has appeared since:

1. **[confidence 96, BLOCKING] Version pin is now a downgrade; R8 AC is
   unsatisfiable.** SPEC.md's version-bump text and R8's AC still target
   `0.8.59`, but `.claude-plugin/plugin.json` is now at **0.9.5** (advanced
   by later merges this run). Bumping "to 0.8.59" would be a downgrade —
   the AC can only pass by regressing the plugin version. Exactly the
   CLAUDE.md failure mode of an acceptance criterion whose numeric bound is
   no longer satisfiable from the file as it exists. Fix: change the
   version-bump text to "bumped from its current 0.9.5 to 0.9.6" and the AC
   to `grep -q '"version": "0.9.6"'` (note: this pin will re-stale again if
   other work merges before this spec is built — a concrete satisfiable
   target is required regardless of how often it needs refreshing).
2. **[confidence 60, nit, non-blocking, carried forward — same as prior
   finding 2] R4's behavioral core still has no verifying check.** Every AC
   for the prototype gate-scaling in build/drain only greps for the literal
   string "Rigor:", proving the header was mentioned, not that the gate
   actually scales; the one manual behavioral AC exercises R2/idea, not the
   R4 build/drain path. Doesn't block /breakdown, cheap to close: add one
   manual-pending behavioral AC exercising the R4 prototype path.

Verified clean: all R8 target paths exist across `.claude/`, antigravity,
and codex mirrors; no unmentioned mirror obligations (codex list-specs is a
symlink into antigravity, no antigravity rules mirror exists so R7 needs
none); every added-string AC anchor still non-vacuous today; the
lint-ultra-gate AC correctly covers this spec's idea/build/drain edits.

Recovery: fix finding 1 (the version-pin downgrade), then re-run /critique.
This spec's critique intake is spent for this run (Run-token
c92aedb1ae49f8d3) — recorded in `DRAIN-BATON.md`'s `Intake-failed:` line.

## Triage 2026-07-14 (attended; Steven approved fix for gen-3 finding 1)

Verdict: fix applied. `.claude-plugin/plugin.json` had moved again by the
time of this triage (0.9.5 → 0.9.8 live) — re-checked fresh rather than
trusting the gen-3 note's 0.9.5. Version-bump text and R8's AC repinned to
"0.9.8 → 0.9.9". Finding 2 (R4 has no verifying check, conf 60, nit)
remains unaddressed and not part of this approval — carried forward.
Re-run `/critique` to check current status.

## Re-critique 2026-07-14 (attended, /critique) — READY WITH NITS

Finding 1's version pin verified accurate against the live tree (0.9.8 →
0.9.9); all R8 target paths, non-vacuous anchors, and the lint-ultra-gate
check confirmed clean. One new finding: R6 (the promotion rule text
itself, not just the `Rigor:` header string) had no acceptance criterion —
a worker could satisfy every runnable AC while never writing the R6 prose.
Fixed: added an AC anchoring the exact promotion-rule phrase ("re-running
the full gates") in both build/SKILL.md and drain/SKILL.md — a plain
`grep -qi "promot"` anchor was tried first and rejected as vacuous, since
drain/SKILL.md already uses that root for unrelated task-promotion
machinery (lines 89, 261, 356-364). The carried-forward R4
behavioral-verification nit (conf 60) remains open and non-blocking.
Re-run `/critique` to confirm READY.
