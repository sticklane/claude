# Critique findings — narrow-autopilot (NOT READY)

Reviewed by drain critique intake, generation 5 (Run-token e83f34f07094a4fa),
2026-07-12. Verdict: **NOT READY** — route to a human to tighten the
acceptance gate and refresh anchors before /breakdown. This is a
high-blast-radius skill retirement (deletes `/autopilot`, edits the
ultra-path `build/SKILL.md` and `drain/reference.md`, sweeps the whole repo,
bumps `plugin.json`), so the bar for an unattended breakdown-and-land is
higher than for a docs spec. The spec is thorough and has no open questions;
the findings below are about verification reliability and drift, not missing
content.

Findings, ranked:

1. **R6 / AC7 grep is non-deterministic across checkout states.** The pinned
   acceptance grep `grep -rln '\bautopilot\b' .claude/ docs/ CLAUDE.md
.claude-plugin/` returns **887 files** in the current main checkout —
   only **19 are git-tracked**; the other ~868 are transient
   `.claude/worktrees/agent-*/` drain worktrees (each a full checkout copy
   containing autopilot mentions). A fresh implementation worktree has no
   nested `.claude/worktrees/`, so a drained worker CAN pass it — but a human
   or verifier running AC7 in the main checkout during any active drain gets
   a false failure. For a whole-repo-sweep gate this non-determinism is a
   defect. Fix: scope it to tracked files —
   `git grep -ln '\bautopilot\b' -- .claude/ docs/ CLAUDE.md .claude-plugin/`
   — or add `--exclude-dir=worktrees`, so the AC is deterministically
   satisfiable regardless of checkout state.

2. **Stale line anchors signal spec drift.** `drain/reference.md:388` (cited
   in R3 and the Problem section) is actually at **line 776**;
   `onboard/SKILL.md:74` is actually at **line 79**. The content-based ACs
   survive the drift, but positional claims like "restructures build/SKILL.md
   ... shifting every line after it" need re-verification against the current
   tree before decomposition — the spec appears to have been authored against
   an older revision.

3. **AC2 verbatim-content check is a manual judgment, not a runnable
   command, and "verbatim" is ambiguous for augmented sections.** The spec
   moves some sections verbatim but augments others (failure recovery moves
   "alongside the walk-away contract's escalation triggers"; the background-
   worktree-agent section is dropped, not moved). "diffed against the old
   autopilot/reference.md to confirm verbatim content" has no runnable form
   and no per-section rule. Specify how each section's verbatim-ness is
   checked (e.g. extract from `git show HEAD:.claude/skills/autopilot/reference.md`
   and compare), and which sections are exempt from strict verbatim because
   they gain adjacent content.

4. **Ultra-path gate missing from acceptance.** `build/SKILL.md` and
   `drain/reference.md` are ultra-path skills; per CLAUDE.md any change to
   them must pass `bash evals/lint-ultra-gate.sh` before commit. The script
   exists but no AC runs it — add it as an explicit acceptance command so a
   drained worker gates on it.

5. **R7 antigravity fold-in is underspecified.** No
   `antigravity/.agents/skills/autopilot/` exists (confirmed), so R7's mirror
   _delete_ is a no-op; but "fold in ... to build's mirror ... only what
   actually applies" leaves the antigravity build-side change undefined.
   Name the concrete antigravity target (skill vs workflow) or state
   explicitly that no antigravity change is required.

6. **Live cross-spec sequencing dependency.** The spec asserts it "should
   land first" before `specs/build-doc-currency-check` (which restructures
   the same `build/SKILL.md`). That sibling is currently NOT READY (in the
   drain Intake-failed set). A human should sequence these two deliberately
   rather than have an unattended drain auto-decompose and auto-land a skill
   deletion in isolation.

Next step for a human: tighten R6/AC7 to a tracked-file grep, refresh the
line anchors (finding 2), make AC2 per-section runnable (finding 3), add the
ultra-gate AC (finding 4), resolve the antigravity fold (finding 5), and
sequence against build-doc-currency-check (finding 6). Then re-run
`/critique specs/narrow-autopilot/SPEC.md`.

## Triage 2026-07-13 (attended; Steven approved REVISE)

Verdict: REVISE. Edits before re-critique: (1) switch R6/AC7 to `git grep` and refresh all anchors (drain/reference.md:873, onboard/SKILL.md:78-79 as of 2026-07-13); (2) rewrite R2/R5 against the post-2026-07-11 launch-contract doctrine (execution stages are live-message-authorized; `/evals` alone keeps disable-model-invocation) — the human-gates edits are stale as written; (3) add the lint-ultra-gate AC, pin per-section verbatim checks, and sequence explicitly before build-doc-currency-check. Verified: `.claude/skills/autopilot/` still exists; recursive grep hits 3282 files vs 21 git-tracked (31 worktrees).

## Re-critique 2026-07-13 (drain critique intake, run b4adb88f) — still NOT READY, approved plan not yet applied

`git log -- specs/narrow-autopilot/SPEC.md` shows no commit since the triage
above — SPEC.md is byte-identical to the state that produced this file's
prior NOT READY verdict. Skipping a redundant full critic dispatch on
unchanged content per token-discipline's "cheap before expensive" — the
three approved triage edits above are the recovery path, unchanged. This
spec's critique intake is spent for this run.

## Re-critique 2026-07-13 (approved triage edits applied) — still NOT READY

The three approved triage edits above were applied to SPEC.md (git-grep
R6/AC7 with refreshed anchors, R2/R5 rewritten against the post-2026-07-11
launch-contract doctrine, lint-ultra-gate AC added, AC2 made per-section
runnable, explicit Sequencing AC added). Re-critiqued via `/critique`.
Verdict: **NOT READY**. The critic confirmed the applied edits are correct
(refreshed anchors match current file content, git-grep scoping is
deterministic, R5's human-gates rewrite is factually accurate, AC2's
per-section check is runnable, the lint-ultra-gate AC is well-placed) but
surfaced findings outside this revision's approved scope:

1. **The codex leg is entirely unaddressed (confidence 88, blocker).**
   `codex/.agents/skills/autopilot/` exists as real content (not a
   symlink) per CLAUDE.md's port-chain rule naming `drain/build/autopilot/
evals` as the four codex wrappers. This spec's R7 addresses only
   `antigravity/`; R6's sweep grep is scoped to `.claude/ docs/ CLAUDE.md
.claude-plugin/`, excluding `codex/` and `antigravity/` entirely, so
   AC7 passing proves nothing about the codex leg. A literal decomposition
   ships `codex/.agents/skills/autopilot/SKILL.md` orphaned and
   `codex/AGENTS.md` + `codex/README.md` stale.
2. **R6's enumeration misses 4 tracked git-grep hits and mis-instructs
   their disposition (confidence 72).** `.claude/rules/
mirror-procedure-discipline.md:55` (historical bug reference),
   `.claude/skills/resume-handoff/SKILL.md:28`, `docs/TASKS.md:54`, and
   `docs/memory/multi-runtime-live-testing.md:62` are in the 21-file
   git-grep set but not in R6's "known hits" list; list-membership hits
   need `/autopilot` dropped from the enumeration (not reworded to
   "build's bounded mode"), and the historical reference should be
   exempted, not rewritten.
3. **Finding 5 (R7 antigravity fold-in underspecified) still stands
   (confidence 65)** — out of this revision's approved scope, so left
   unchanged, but not resolved: whether `antigravity/.agents/skills/
build/` needs the new classification gate/escalation triggers ported
   is still undefined.

Next step for a human: findings 1–2 need the same triage-and-approve
treatment as the prior round before another revision round; finding 3
repeats prior finding 5, unresolved by design this round.

## Triage 2026-07-13 (attended; Steven approved, walk-through item 21)

Verdict: REVISE, applied directly. Resolves findings 1-3 and goes further
than the critic's own finding 1 asked for — investigation surfaced that
R7's original antigravity check was wrong-scoped, not merely unspecified:

1. **Codex leg (finding 1, blocker) — new R7a.**
   `codex/.agents/skills/autopilot/` confirmed real content (SKILL.md +
   agents/openai.yaml, not a symlink); deletion + fold-in into
   `codex/.agents/skills/build/SKILL.md` now required. R6 extended to
   sweep `codex/` too and covers `codex/AGENTS.md`, `codex/README.md` (4
   mentions), `drain/SKILL.md`, `evals/SKILL.md` — each drops autopilot
   from "the four" to the three-skill set. CLAUDE.md's own codex-leg
   authoring convention (2 separate mentions, not the 1 previously named)
   gets the same three-skill fix — a doctrine change, not a
   grep-and-reword, called out explicitly so a drained worker doesn't
   under-scope it to a literal find-replace.
2. **R6's 4 missed hits (finding 2) — dispositioned individually.**
   `resume-handoff/SKILL.md` and `docs/TASKS.md` and
   `multi-runtime-live-testing.md`: `/autopilot` dropped from their
   enumerations (list-membership, not reworded). `mirror-procedure-
discipline.md`: exempted (historical bug citation, not living
   doctrine) — joins the existing `orchestration-research-2026-07.md`
   exemption.
3. **Antigravity fold-in (finding 3) — corrected, not just resolved.**
   The original R7 hedge checked `antigravity/.agents/skills/autopilot/`
   (absent) and concluded there was nothing to mirror. Direct inspection
   found the real mirror lives at `antigravity/.agents/workflows/
autopilot.md` (90 lines, real content) — autopilot is ported as a
   _workflow_, not a skill, matching CLAUDE.md's own port-chain
   convention for human-only skills. R7 rewritten to delete that file and
   fold its content into `antigravity/.agents/workflows/build.md`. R6
   extended to also cover `antigravity/README.md`, `gate/SKILL.md`,
   `resume-handoff/SKILL.md`, and `drain.md`'s own autopilot mentions.

Acceptance criteria extended to match: the R6 grep AC now scopes to
`codex/` and `antigravity/` too (31 tracked files today, must drop to
exactly the 2 exempt files), new ACs for the antigravity workflow and
codex skill fold-ins, and a CLAUDE.md three-vs-four doctrine check. Also
fixed a formatter-introduced markdown nesting regression in the existing
`build/reference.md` per-section AC (unrelated to the findings, caught in
passing).

Ready for re-critique.

## Re-critique 2026-07-14 (drain critique intake, gen 3, run c92aedb1ae49f8d3) — still NOT READY

All prior-round fixes verified still landed and accurate (human-gates.md
anchors, onboard/gate/breakdown mentions, CLAUDE.md's 3 hits, the
antigravity workflow + codex skill fold-in targets, both exempt files
present). Three new gaps, all caused by the live tree moving since last
verification (qa-sweep-skill-promotion's task 03 merged an antigravity
mirror after this spec's last check):

1. **AC7 is unsatisfiable as written — an uncovered `/autopilot` hit now
   exists in `antigravity/.agents/skills/qa-sweep/SKILL.md:82`
   (confidence 88).** The verifying grep now returns 32 tracked files, not
   the 31 the spec pins. The new hit — `"(build/autopilot/drain/prioritize),
so no live-request naming it is required"` — landed via the qa-sweep
   antigravity mirror (commit `225ff0f`) after this spec's last
   verification. It's covered by zero requirements/Touch scopes (the spec
   never mentions "qa-sweep"), and it exists only in the antigravity leg —
   the `.claude` source has zero autopilot mentions. Fix: add
   `antigravity/.agents/skills/qa-sweep/SKILL.md` to R6's antigravity
   enumeration (three-skill-set treatment) and update AC7's count to 32.
2. **`drain/reference.md` has a second `/autopilot` mention (line 158,
   the "Orchestrator isolation" paragraph) that R3 doesn't address, plus a
   stale anchor (confidence 78).** R3/Problem cite `:884` for the headless
   citation; it's now `:1007`. R6 excludes reference.md as "handled by
   R1-R5," but R1-R5 only cover the headless citation, not line 158's
   isolation-scope mention. AC7 would catch this as a backstop (not a
   silent miss like finding 1), but the Touch scope and edit instructions
   should name both mentions explicitly. Fix: R3 notes both mentions
   (headless ~:1007, isolation-scope ~:158), both updated; refresh anchor.
3. **AC7's pinned count (31) is already stale one day after authoring
   (confidence 75, spec-tier).** The mirror set churns day-to-day (qa-sweep
   landed between authoring and now); a count-based AC on a moving target
   will keep breaking. The content-based per-file checks are robust; the
   raw count is the fragile part. Fix: state AC7 as "returns exactly the 2
   exempt files (docs/orchestration-research-2026-07.md,
   .claude/rules/mirror-procedure-discipline.md)" and drop the absolute
   count, or re-derive it at breakdown time.

Recovery: fix findings 1-3, then re-run /critique. This spec's critique
intake is spent for this run (Run-token c92aedb1ae49f8d3) — recorded in
`DRAIN-BATON.md`'s `Intake-failed:` line.

## Fix applied 2026-07-14 (attended, human-authorized HUMAN.md cleanup pass)

All three findings fixed directly in SPEC.md, re-verified live against the
current tree (32 tracked autopilot hits today, up from 31, confirming
finding 1's premise):

1. R6's antigravity enumeration now includes
   `antigravity/.agents/skills/qa-sweep/SKILL.md` (the newly-landed mirror
   hit at its current line 82), with the same three-skill-set treatment
   as its siblings.
2. R3 now names BOTH of `drain/reference.md`'s `/autopilot` mentions
   (`:1007`'s headless-rule citation and `:158`'s "Orchestrator isolation"
   paragraph), with anchors refreshed and explicitly marked as snapshots.
3. AC7 dropped its stale pinned count entirely — the gate condition was
   already the count-independent "returns exactly the 2 exempt files"
   form, so this was a cosmetic/informational fix (removing the
   misleading "(currently 31 tracked files...)" parenthetical) rather
   than a substantive one; added a note stating the count is deliberately
   not gated on, since the mirror set churns day to day.

Ready for re-critique.

## Re-critique 2026-07-14 (attended, /critique) — one leftover anchor found

A fresh critic dispatch found the qa-sweep enumeration, the second
drain/reference.md mention, and the AC7 count fix (findings 1 and the
"both mentions named" half of finding 2 above) already correctly landed
— verified directly against the live tree. One thing was missed by the
prior pass: the `:884` anchor for `drain/reference.md`'s headless-rule
citation was never actually refreshed to its current `:1007` in three
prose spots (Problem section, R3's Headless-template bullet), despite
the "Fix applied" note above claiming anchors were refreshed. Also
refreshed `breakdown/SKILL.md:98` → `:166` (stale since this spec's
authoring; the routing sentence moved when breakdown/SKILL.md grew).
Both confirmed accurate against the live files. Re-run `/critique` to
confirm READY.

## Re-critique 2026-07-14 (attended, /critique) — a real doctrine-corruption bug found

The anchor fixes verified accurate. But a fresh pass caught something
serious: R6's CLAUDE.md sub-bullet quoted STALE pre-2026-07-11 text for
the execution-stages doctrine line ("Execution stages (`/build`,
`/autopilot`, `/drain`, `/evals`) keep `disable-model-invocation: true`")
that doesn't match live CLAUDE.md:36 at all, and prescribed dropping
`/autopilot` → "`/build`, `/drain`, `/evals`" — which is factually wrong:
line 36 is the model-invocable list, and `/evals` is explicitly the ONE
stage CLAUDE.md pins as never model-invocable, three sentences later. A
worker following this verbatim would corrupt CLAUDE.md's own launch-
authorization doctrine while passing every existing AC (none of them
pinned line 36's actual outcome). Fixed: reworded R6's sub-bullet to
quote CLAUDE.md's live text and state the correct target
("`/build`, `/drain`, `/prioritize`", explicitly not `/evals`), and added
a new AC pinning that exact phrase (confirmed both the correct and the
wrong phrase are absent today, i.e. non-vacuous either way). Also fixed a
minor count nit: R6 said `codex/README.md` had "4 mentions", live count
is 5 (lines 17, 22, 89, 121, 129) — corrected, backstopped either way by
AC7's whole-file sweep. Re-run `/critique` to confirm READY.

## Re-critique 2026-07-14 (attended, resumed from handoff) — NOT READY, R6 sweep excluded 7 trees

Fresh critic pass found R6's prose promised a "whole repo" sweep but its
verifying grep scoped to only `.claude/ docs/ CLAUDE.md .claude-plugin/
codex/ antigravity/`, silently excluding `evals/`, `runtimes/`,
`README.md`, `AGENTS.md`, `bin/`, `tests/`, and `agent-console/` — each
confirmed to hold a living `/autopilot` reference, including a whole
orphaned evalset (`evals/autopilot/01-security-refusal/`) and stale gate
machinery (`bin/check-token-discipline`'s `IN_SCOPE` list pointing at
paths R1 deletes). Fixed: broadened the swept pathspec, named every
newly-found file's disposition (delete/reword), added two more
exemptions for genuinely historical mentions, added three new ACs, and
cross-checked by re-running the full broadened sweep — every hit
accounted for. Commit ef44c54.

## Re-critique 2026-07-14 (attended, resumed from handoff) — READY WITH NITS

Fresh critic pass ran the exact broadened grep and cross-checked all 42
hits against the spec's enumeration — everything accounted for, every
newly-added disposition verified factually accurate against live files.
One more gap found: `gate/SKILL.md` has TWO `/autopilot` mentions, not
one — R4 only named the closing `Next stage:` line, missing the prose
sentence just above it ("...tasks qualify for `/autopilot`"). Backstopped
by AC7 (gate/SKILL.md isn't exempt, so it can't ship with a stray
mention), but a worker would have had to improvise the rewording with no
guidance, unlike every other file in R6. Fixed: R4's gate bullet now
names and rewords both lines explicitly. This spec is now READY WITH
NITS — ready for `/breakdown`.
