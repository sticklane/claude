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
   *delete* is a no-op; but "fold in ... to build's mirror ... only what
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
