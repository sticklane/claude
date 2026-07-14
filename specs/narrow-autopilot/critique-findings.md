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
