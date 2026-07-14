# Critique findings — NOT READY (2026-07-11, drain critique intake, gen 3)

Critic verdict: NOT READY. Ranked findings (most damaging first):

1. **Codex mirror leg omitted entirely** (confidence 88). R4/R5 change
   `.claude/skills/build/SKILL.md`, but the spec names only the
   `antigravity/` mirrors (R6), never `codex/`. Per CLAUDE.md's codex rule,
   `codex/.agents/skills/build/SKILL.md` is real content (verified: not a
   symlink, carries the same close-out step and code-review invocation R4/R5
   target) and must ride in the closing task's `Touch:` with a matching
   acceptance criterion — an unlisted mirror silently ships un-updated.

2. **R1 placement contradicts the Out-of-scope exclusion** (confidence 80).
   R1 puts the discipline in `.claude/rules/quality-discipline.md`, which
   binds workers "attended or unattended" (and untrusted-data.md binds
   unattended workers to `.claude/rules/`), yet Out-of-scope (lines 99-103)
   excludes `/drain`'s unattended workers. Decide and state: scope the rule
   text to the attended `/build` completion path, or drop the exclusion.

3. **Acceptance criteria are prose, not runnable commands; no codex AC**
   (confidence 65). ACs at lines 107-119 are not mechanically pass/fail.
   `grep -c "Documentation currency"` → 0 across all four named targets
   today (verified — valid absent anchor); convert each AC to a grep on the
   confirmed-absent literal and add the codex target.

4. **Stale line anchors beyond the hedge** (confidence 55, nit). R5 cites
   `build/SKILL.md:86` (actual :143); R4 "~line 77" (actual :133); R6
   `antigravity/.agents/workflows/build.md:63` (actual :111, unhedged).
   Drop numeric anchors or hedge the antigravity ones as snapshots.

Verified accurate: no `.claude/skills/code-review/` exists; narrow-autopilot
not yet broken down (sequencing dependency live); `antigravity/AGENTS.md`
`## Quality discipline` exists for R6; no duplication of gate skill, drain
spec-completion review, or lint-ultra-gate.sh.

Next step: amend SPEC.md per findings 1-3 (4 optional), then re-run
/critique. Recorded by drain gen 3 (run e83f34f07094a4fa); this spec's
critique intake is spent for this run (Intake-failed baton line).

## Re-critique 2026-07-13 (drain critique intake, run a219d53e) — still NOT READY

Spec unchanged since the 2026-07-11 NOT READY verdict; all four findings
stand (codex mirror leg omitted from R6/Touch; R1 rule placement contradicts
the Out-of-scope drain exclusion; acceptance criteria not runnable anchored
greps; stale numeric line anchors — R6's antigravity :63 is actually :121).
Recovery: amend SPEC.md per findings, then re-run /critique.

## Triage 2026-07-13 (attended; Steven approved REVISE)

Verdict: REVISE. Edits before re-critique: (1) extend R6 to the codex leg with an inline one-line reminder (codex/.agents/skills/build/ is real content with no citable quality-discipline file); (2) scope R1's rule text to the attended /build path or drop the drain exclusion; (3) convert ACs to anchored greps and drop numeric line anchors. Verified: `grep -c "Documentation currency"` → 0 in both targets (problem unsolved); no existing gate covers doc drift.

## Re-critique 2026-07-13 (drain critique intake, run b4adb88f) — still NOT READY, approved plan not yet applied

SPEC.md is byte-identical to before the triage — only critique-findings.md was
updated in the 2026-07-13 triage commit, none of the three approved edits
landed in SPEC.md itself. Critic re-verified independently (codex
build/SKILL.md real content with `$code-review` at line 146, no
quality-discipline rule file on the codex leg; `grep -c "Documentation
currency"` → 0 across all five targets) and confirms the same three findings
stand verbatim, plus one new nit:

1. Codex mirror leg still absent from R6 and the acceptance criteria
   (confidence 90) — same as prior rounds, triage edit (1) unapplied.
2. R1 rule placement still contradicts the Out-of-scope drain exclusion
   (confidence 85) — triage edit (2) unapplied.
3. Acceptance criteria still prose, not runnable greps; stale numeric line
   anchors remain (confidence 82) — triage edit (3) unapplied.
4. NEW (confidence 62, nit): build is an ultra-path skill —
   `bash evals/lint-ultra-gate.sh` isn't named in the verification steps;
   should stay green after the edit and be called out explicitly.

Recovery: apply the three approved triage edits to SPEC.md itself (not just
recorded in this file), add the lint-ultra-gate note, then re-run /critique.
This spec's critique intake is spent for this run.

## Re-critique (drain critique intake) — still NOT READY, edits landed with new gaps

Findings 1-3 from the prior round landed in SPEC.md's Requirements this time
(codex leg added to R6, R1 rescoped, ACs converted to anchored greps), but
introduced a self-contradicting artifact — SPEC.md gained its own embedded
`## Critique findings (2026-07-13)` section asserting NOT READY on top of the
now-fixed Requirements — plus new gaps surfaced underneath the fix:

1. R4's AC demands capital "Documentation currency" but R4's own example
   citation text was lowercase "documentation currency" — the edit could
   satisfy R4's prose and still fail its own AC (conf 78).
2. R5's AC (`grep -c "quality-discipline"`) overlapped with R4's citation
   text (which also contains "quality-discipline.md"), so R5's edit wasn't
   independently verified — R4's edit alone could satisfy both ACs (conf 74).
3. R6's antigravity citation named `quality-discipline.md`, a file that
   doesn't exist in antigravity — its real equivalent is `AGENTS.md`'s
   `## Quality discipline` section (conf 70).
4. The embedded `## Critique findings` section in SPEC.md itself still
   asserted NOT READY and described already-fixed problems as current,
   self-contradicting if the spec were fed to `/breakdown` (conf 70).

## Triage 2026-07-13 (attended; Steven approved, walk-through item 18)

Verdict: REVISE, applied directly (not just recorded — low-risk spec-text
edit, same pattern as the prior triage). Fixes landed in SPEC.md:

1. R4's example citation reworded to name the section by its proper noun
   ("see quality-discipline.md's Documentation currency section") so it
   matches the AC's capitalization naturally, instead of a case mismatch.
2. R5's citation and AC reworded onto a distinct anchor
   (`"not by /code-review itself"`) that R4's edit cannot satisfy alone —
   verified absent today via `grep -c`.
3. R6's antigravity citation reworded to name `AGENTS.md`'s Quality
   discipline section instead of the nonexistent `quality-discipline.md`;
   antigravity ACs split into two independently-anchored checks
   (`"Quality discipline section"` for the R4-equivalent citation,
   `"not by the sub-reviewer fallback"` for the R5-equivalent note) —
   both verified absent today.
4. The stale embedded `## Critique findings (2026-07-13)` section removed
   from SPEC.md entirely (this file is where critique history belongs,
   per this spec's own multi-round convention) — findings 1/2/4 above were
   already fixed by the Requirements edits; finding 3 (lint-ultra-gate.sh
   not named) got a new acceptance-criterion bullet instead.

Ready for re-critique.
