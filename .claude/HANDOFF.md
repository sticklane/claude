# Handoff: transcript-antipattern specs + agentprof follow-up

Session ended per token-discipline.md's Session refresh doctrine (1
re-prime, 266k p90 context, over the default wake budget).

## Task

Two specs written from an 11-session transcript audit for token-inefficiency
antipatterns, both at `specs/<slug>/SPEC.md`. Plus an in-conversation
agentprof analysis (findings below) not yet turned into a spec.

## State

- `specs/drain-read-once-discipline/SPEC.md` — **READY**, `Breakdown-ready: true`
  header already written. Two critique rounds, all findings fixed. No further
  action needed except running `/breakdown` on it (self-chains, or run
  manually) when the user wants to proceed to implementation.
- `specs/drain-plugin-path-resolution/SPEC.md` — fixes for the first critique
  round's 3 NOT READY findings are applied and hand-verified against disk
  (all new/changed grep anchors confirmed correct — see Gotchas), but **not
  yet re-run through `/critique`**. That's the immediate next step.
- Neither spec has a `tasks/` directory yet (no `/breakdown` run).
- No spec exists yet for: (a) the frontier-tier-critique-model cost issue,
  (b) the agentprof tool enhancements. User was asked which (if any) to spec
  next; no answer arrived before the session ended.

## Immediate next step

1. `/critique specs/drain-plugin-path-resolution/SPEC.md` — verify the 3
   fixes (see Gotchas for what they were) actually satisfy the critic fresh.
   On READY, add `Breakdown-ready: true` under the title (same line the
   sibling spec already has).
2. Ask the user: spec out the frontier-tier-critique fix and/or the
   agentprof changes (both described below), or move straight to
   `/breakdown` on the two ready specs?

## Files touched this session

- `specs/drain-read-once-discipline/SPEC.md` — new, READY.
- `specs/drain-plugin-path-resolution/SPEC.md` — new, fixes applied, awaiting
  re-critique.
- Nothing else in the repo was edited — both specs are additive, no existing
  file outside `specs/` was touched.

## Gotchas / things learned this session (don't re-derive)

- **`drain-read-once-discipline` targets a real, narrow gap**: a prior spec
  (`drain-hub-context-discipline`, already merged) fixed _whole-file_ reads
  of `reference.md`; it did NOT fix _re-reading the same already-loaded
  section_ a second time with no edit in between. These are different bugs.
  The new spec's canonical phrase is **"already loaded this section this
  session"** — verbatim, required in `reference.md` AND both mirrors AND the
  manifest entry (divergence-exempt from normal mirror-prose freedom). The
  concurrency-guard exemption phrase is **"Status-flip concurrency guard"**
  — also verbatim-pinned, added in the second critique round as a nit-fix.
- **`drain-plugin-path-resolution` root cause**: `reference.md:641-642` says
  a path resolves to "the plugin cache path found at dispatch" with no
  concrete procedure. Two real sessions guessed a stale version
  (`agentic/0.9.19/...`) instead of checking — `0.9.19` is a real past value
  that still appears in several committed spec/evidence files, so the guess
  wasn't random. `bin/plugin-installed-version` (reads `claude plugin list
--json`) already solves version lookup and is tested
  (`tests/test_plugin_version_helper.sh`). Live-confirmed during this
  session: installed plugin cache is at
  `~/.claude/plugins/cache/agentic-toolkit/agentic/0.9.21/` — one patch
  ahead of this dev checkout's `plugin.json` (`0.9.20`) — a real, current
  illustration of the drift.
- **The 3 fixes applied to `drain-plugin-path-resolution` after its NOT
  READY verdict**: (1) split the resolution recipe into Step 1 (in-repo
  check — portable, mirror it) vs. Step 2 (the
  `$HOME/.claude/plugins/cache/agentic-toolkit/...` construction —
  Claude-Code-specific, load-bearing, must NOT be copied into
  antigravity/codex mirrors — confirmed via disk read that
  `antigravity/.agents/workflows/drain.md` and
  `codex/.agents/skills/drain/SKILL.md` genuinely have no equivalent branch);
  (2) added a positive acceptance check
  (`grep -q "plugins/cache/agentic-toolkit/agentic" .claude/skills/drain/reference.md`,
  confirmed absent today) since the original only checked the old vague
  phrase was _removed_, which was gameable by deletion-without-replacement;
  (3) constrained R6's deferred manifest phrase to the portable procedural
  line only, never the Claude-Code-specific cache-path literal. All grep
  anchors for these three re-verified against current disk state — commands
  and results are in the SPEC.md's Acceptance criteria section, not repeated
  here.
- **agentprof** (`agentprof/` in this repo, a Go pprof-based cost profiler)
  was actually built and run (`go build -o agentprof .`, then
  `agentprof claude --days 7`) — not just read about. 45,632 samples,
  $3,960.78 total 7-day spend. Key numbers, in case a future spec needs
  them: `skill:drain` = $1,692.89 (43%); reprime/cache-rewrite cost =
  $595.25 (15.0%), concentrated in `skill:critique` and
  `skill:drain > stage:collect-verdict` running under `claude-fable-5`
  (frontier tier) in the `fooszone` and `(home)`/automation projects — this
  directly contradicts `reference.md`'s own "run the drain hub on opus tier
  or below" doctrine; `agent:general-purpose` = $336.33 (2nd-highest agent
  bucket); 13.6% of samples (6,227/45,632) are unattributed (orphaned
  tool-call fallback, zero cost/token data). Confirmed via real JSONL
  inspection: agentprof's schema has NO file-path or per-tool-call
  granularity for normal samples (the `tool:*` stack frame exists but is
  populated only for the orphaned 13.6%), so it structurally cannot detect
  the redundant-read antipattern on its own — this is a genuine capability
  gap, not just an unused flag.

## Verification

- `drain-read-once-discipline`: all acceptance-criteria grep anchors
  hand-verified against disk during authoring (results inline in the
  SPEC.md's own criteria text with verification dates). No verifier agent
  run — nothing was implemented yet, only the spec itself, which went
  through two critic rounds instead.
- `drain-plugin-path-resolution`: same — critic-reviewed once (NOT READY),
  fixes applied, anchors hand-verified, but the critic has not yet
  confirmed the fixed version. Do not treat it as READY until step 1 above
  completes.
