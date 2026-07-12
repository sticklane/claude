# Mirror procedure discipline: stop hand-mirroring the same procedure three times

Breakdown-ready: true

## Problem

Two scout passes this session compared every mirrored skill's actual
PROCEDURE — not just prose or file existence — between `.claude/skills/`
(source), `antigravity/.agents/` (a full mirrored port), and
`codex/.agents/skills/` (mostly symlinks to antigravity, plus four
real-content skills). They found real behavioral drift the existing gates
cannot catch: `antigravity/.agents/workflows/drain.md` was missing an entire
"Environment kill" procedure; `antigravity/.agents/workflows/autopilot.md`
silently dropped an alternative precondition path; `codex/.agents/skills/
autopilot/SKILL.md` told the model to use CLI flags (`--allowedTools`,
`--max-turns`) that `runtimes/codex.md`'s own documented capabilities say
don't exist for `codex exec`. Five more incidental gaps (missing steps in
critique's mirror, a lost `Unblock:` grammar nuance in breakdown's mirror, a
missing parallelism count in idea's mirror, a missing classification-gate
checklist item in drain's mirror, two doctrine rules in swapped order in
build's mirror) were found and fixed the same way: read both files in full,
by hand, this session.

This is NOT the gap `specs/mirror-verification-discipline` already closed —
that rule covers cross-references (paths, commands, tool names) that look
fine in a diff but don't resolve under the target runtime, verified by
exercising the mirror live. It is explicitly not about procedural content:
its own sibling spec (`codequality-antigravity-content-parity`) scopes byte-
diffing to `.py` files only, "since a mirror is a port, not a copy, and
prose legitimately diverges between runtimes." This spec's gap is different:
even where prose is *expected* to diverge (a mirror is a port), the
underlying PROCEDURE — the actual sequence of steps, decision points, and
behaviors a skill instructs — is not supposed to diverge, except where a
runtime's own mechanism forces it (a different launch-gating primitive,
tool names, headless invocation shape). Nothing currently distinguishes
"this divergence is inherent to the runtime" from "this divergence is
prose-level drift in what's supposed to be the same procedure," and nothing
catches the latter except a full by-hand read — which this session did for
6 of 19 skills at real, nontrivial cost.

A scout pass (`runtimes/parse_headless.py` + `runtimes/*.md`) already proves
one shared-mechanism pattern works well in this repo: ONE parser serves
every runtime's headless-invocation template and tier language without
per-consumer special-casing. But it works because headless templates and
tier tables are static text substitution. A follow-up scout pass confirmed
this pattern does NOT generalize cleanly to branching, stateful procedures
(drain's dispatch/collect/baton-pass loop) without inventing a genuine
runtime-agnostic procedure DSL — a much bigger lift than "extend it one
level further." This spec deliberately does not attempt that. Instead it
extends a DIFFERENT existing pattern that already works in this repo:
skills cite `.claude/rules/*.md` by name instead of restating rule content
inline (`runtimes/README.md` states this as its own guiding principle for
tier language). The same discipline — write invariant content once, cite it
rather than re-derive it — applies to procedural content too.

## Solution

**1. A citation-discipline authoring rule.** Add
`.claude/rules/mirror-procedure-discipline.md` (matching the format of
`mirror-verification.md`: short H1, terse prose, `##`
subsections). States: when a skill's procedural content is invariant across
runtimes — the same algorithm, decision tree, or step sequence, not
something a runtime's own mechanism forces to differ — a mirror must carry
that content faithfully (same steps, same order, same stated conditions),
not independently re-derive, abbreviate, or reorder it. The only content
that's allowed to diverge in substance (not just wording) is what's
load-bearing: a different launch-gating primitive, a different dispatch
tool, a different headless invocation shape, a capability the target runtime
genuinely lacks. When authoring or editing a mirror, classify each
divergence into one of these two buckets before deciding whether to leave
it — the same classification this session's two scout passes used to find
the 8 real gaps.

**2. An advisory, heuristic parity-coverage check.** A new script,
`tests/test_mirror_procedure_coverage.sh`, added to the existing test sweep
(`tests/test_*.sh`, run manually today — same status as the existing parity
tests, not wired into CI or a blocking gate). It maintains a small, curated
manifest (`tests/mirror-procedure-manifest.txt` or similar: `<source
file>|<mirror file>|<critical phrase>` lines) of specific phrases or
concepts that must appear in both a source file and its mirror — seeded
from the 6 manifest-expressible of this session's 8 fixes (e.g.
`drain/reference.md|antigravity/.../drain.md|Environment kill`) so a future
edit can never silently re-drop them. The script greps each manifest line's phrase in both files and fails
(non-zero exit, listed in the test sweep's FAIL output) if the source has it
and the mirror doesn't. This is deliberately a coverage heuristic, not a
semantic-equivalence checker — full procedural-equivalence checking stays a
by-hand or agent-driven read, per `mirror-verification.md`'s existing
closure-triggered-sweep cadence, which this rule cites rather than
duplicates. The manifest grows every time a future session finds and fixes
a real procedural gap — never shrinks silently.

**3. Retrofit audit across all applicable skills.** Of the 19 skills under
`.claude/skills/` (excluding `_shared`), 17 have some antigravity artifact
(a `skills/<name>/SKILL.md` and/or `workflows/<name>.md`); `fleet` and
`workflow-author` have none and are legitimately out of scope (Claude
Code-specific: fleet visualizes this session's own agent tooling, and
workflow-author generates Workflow-tool scripts for a tool Antigravity does
not have — `antigravity/.agents/workflows/critique.md` already documents
"Antigravity has no Workflow tool"). Of those 17, this session's two scout
passes plus fixes already covered 6: `autopilot`, `breakdown`, `build`,
`critique`, `drain`, `idea`. The remaining 11 — `design`, `distill`,
`evals`, `factcheck`, `gate`, `handoff`, `list-specs`, `onboard`,
`prioritize`, `prose-review`, `workboard` — need the same by-hand
side-by-side procedural read this session gave the first 6, applying the
bucket classification from part 1, fixing incidental (bucket 2) divergence,
and adding any fix's critical phrase to part 2's manifest. Separately,
Codex's four real-content skills (`autopilot`, `build`, `drain`, `evals`)
need the same audit specifically for Codex-vs-source divergence — `autopilot`
and `evals` were already checked this session (autopilot fixed; evals found
load-bearing-only, no fix needed); `build` and `drain` still need it.

## Requirements

- R1: `.claude/rules/mirror-procedure-discipline.md` exists, matches the
  format of `.claude/rules/mirror-verification.md` (short H1, terse
  declarative prose, `##` subsections, citations in parentheses rather than
  restated inline), and states the two-bucket classification (load-bearing
  vs. incidental divergence) as its central rule. The file also names R3's
  heuristic's two known blind spots explicitly (ordering-only divergence,
  and a mirror asserting content absent from the source rather than missing
  source content) so a reader doesn't mistake a passing gate for a complete
  check.
- R2: The rule file explicitly distinguishes its scope from
  `mirror-verification.md` (cross-reference resolution) — this rule governs
  procedural/behavioral content, not links, paths, or commands — so a
  reader doesn't conflate the two or think either one supersedes the other.
- R3: `tests/test_mirror_procedure_coverage.sh` exists, is added to the
  test sweep pattern (`tests/test_*.sh`), reads a manifest file, greps each
  manifest line's phrase against its named source and mirror files, and
  exits non-zero with a clear per-line failure message when a phrase is
  present in the source but absent from the mirror.
- R4: The manifest is seeded with entries covering the 6 of this session's 8
  fixes that fit the source-has/mirror-lacks phrase shape (3 in commit
  `e742cb6` minus the codex autopilot fix, 5 in commit `4d1edcc` minus the
  build.md reorder — grep those commits' diffs for the exact added phrases),
  so re-running the script immediately after this spec lands passes cleanly
  and would have caught those 6 gaps had it existed beforehand. The
  remaining 2 fixes are NOT manifest-expressible and are not forced in: the
  build.md fix was a pure reorder (the phrase is present in both files
  before and after, so a presence check can't detect it), and the codex
  autopilot fix replaced wrong mirror-only content with codex-specific
  correct content that has no equivalent phrase in the Claude Code source.
  Both are logged as R1's stated blind spots, not manifest entries.
- R5: Each of the 11 not-yet-audited antigravity skills listed in the
  Solution section is read side-by-side against its source and reconciled:
  any found incidental divergence is fixed, matching the pattern of this
  session's 8 fixes (small, targeted edits — not a rewrite), and a
  corresponding manifest entry is added for anything fixed and
  manifest-expressible per R4's shape. A skill with zero divergence found,
  or with divergence found but not manifest-expressible, still gets a
  one-line "checked: <finding or clean>" entry appended to
  `tests/mirror-procedure-manifest.txt` itself (a comment line, not a check
  line — same file R3/R4 already touch, so no second shared mutable file is
  introduced) confirming it was checked, so "not yet audited" never gets
  silently conflated with "audited, found clean."
- R6: Codex's `build` and `drain` real-content skills are read side-by-side
  against both their Claude Code source AND their Antigravity counterpart
  (the three-way comparison the first scout pass used for Codex's
  `autopilot`), any found Codex-specific incidental divergence is fixed,
  and a manifest entry is added for anything fixed.
- R7: No requirement above authorizes inventing a build-time codegen or
  procedure-DSL mechanism — citation discipline (R1) plus the heuristic
  gate (R3) are the whole mechanism; a future spec may revisit codegen if
  citation discipline proves insufficient, but that decision is explicitly
  deferred, not made here.

## Out of scope

- `fleet` and `workflow-author` — no antigravity artifact exists for either,
  and both are genuinely Claude Code/Workflow-tool-specific; nothing to
  reconcile.
- Any build-time codegen, procedure-DSL, or single-source-with-transclusion
  mechanism (R7) — evaluated and explicitly deferred, not adopted, per the
  scout finding in the Problem section that the existing `runtimes/*.md`
  pattern doesn't generalize to branching procedures without inventing new
  infrastructure.
- Making the new parity-coverage check (R3) a blocking gate (Stop hook,
  pre-commit, or required CI status) — it stays advisory, run manually in
  the test sweep exactly like the existing `test_antigravity_parity.sh` and
  `test_codex_parity.sh`, which also aren't wired into CI today.
- Codex's 15 symlinked skills — fixing their antigravity target (R5) fixes
  the Codex side automatically, since a symlink has no separate content to
  diverge.
- Retrofitting `.claude/skills/` (the source) itself — this spec only
  reconciles mirrors against the existing source; source-side skill
  improvements are out of scope.

## Acceptance criteria

- [ ] `test -f .claude/rules/mirror-procedure-discipline.md` (R1)
- [ ] The rule file's text contains both "load-bearing" and "incidental"
      as its named divergence buckets, and a line distinguishing its scope
      from `mirror-verification.md` (R1, R2)
- [ ] `bash tests/test_mirror_procedure_coverage.sh` exits 0 (R3, R4)
- [ ] `grep -c "Environment kill" tests/mirror-procedure-manifest.txt` (or
      equivalent manifest path) → ≥1, confirming the drain fix is
      manifest-covered (R4)
- [ ] For each of the 11 listed skills, either a diff exists in this spec's
      task commits touching its antigravity mirror, or a "checked:" comment
      line for it exists in `tests/mirror-procedure-manifest.txt` (R5)
- [ ] `codex/.agents/skills/build/SKILL.md` and `codex/.agents/skills/
      drain/SKILL.md` each have either a fix-diff or a "checked:" comment
      line in the manifest (R6)
- [ ] `for t in tests/test_*.sh; do bash "$t" || echo "FAIL: $t"; done`
      prints no FAIL lines (full regression sweep, all prior fixes still
      hold)
- [ ] `bash evals/lint-ultra-gate.sh` → exit 0
- [ ] End-to-end: pick one of the 11 not-yet-audited skills at random after
      breakdown, verify its assigned task's diff (if any) actually closes a
      real divergence found by manually reading both files — not merely
      that the task file claims completion.

## Open questions

(none)

## Parallelization

Each of the 11 remaining antigravity skill audits (R5) plus the 2 Codex
audits (R6) is an independent read-and-fix over disjoint file pairs. They
do share one mutable file — the manifest (R3/R4), which every task appends
to (both check-line entries and "checked:" comment lines) rather than
rewrites. Under `/drain` worktree isolation, two branches that both append
at end-of-file can produce a trivial git merge conflict (both insert after
the same last line) — expected, not a design flaw; drain's sequential
per-task merge resolves each in turn, so this doesn't block concurrency,
it just means the manifest file itself is never a candidate for a
concurrent-writer group of its own. R1-R4 (the rule file + the gate
script + its initial seed) should land as one task before the audits begin,
since R5/R6 tasks cite the rule's bucket classification and append to the
manifest R3/R4 create. After that, all 13 audit tasks (11 antigravity + 2
Codex) form one large concurrent-safe group, suitable for `/drain` with a
rolling window.

- Group: 02, 03, 04, 05, 06, 07, 08, 09, 10, 11, 12, 13, 14
