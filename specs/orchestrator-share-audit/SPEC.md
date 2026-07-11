# Orchestrator-share audit for /breakdown, /build, /idea

Status: open
Priority: P2

## Problem

agentprof (2026-07-04→11; see ../drain-wake-cost/EVIDENCE.md) measured the
main-line (orchestrator) share of each orchestration skill's cost:

| Skill | main-line $ | delegated $ | orch share |
|---|---|---|---|
| /parallel | 4.54 | 25.83 | 15% |
| /drain | 194 | 186 | 51% |
| /idea | 81 | 34 | 70% |
| /build | 58 | 16 | 78% |
| /breakdown | 142 | 27 | 84% |

The puzzle: /breakdown, /build, and /idea already carry explicit "don't read
the codebase into this session — use scouts" doctrine, yet 70–84% of their
spend stays in the frontier-priced main context. Either the doctrine isn't
followed in practice, or the main-line work these skills legitimately do
(interviewing, decomposing, writing task files) is intrinsically expensive
at frontier rates and should be restructured, or the cost is cache-rewrite
overhead unrelated to reading. We don't know which — the per-skill totals
can't distinguish them. Restructuring before measuring risks fixing the
wrong thing.

Measurement constraint (verified against agentprof internals): cost lives
only on model-call samples; `tool:` frames carry `duration_ms` only and NO
file paths (sample emission drops tool_use input entirely). So "dollars
attributable to file Reads" is NOT derivable — once read, file content is
indistinguishable accumulated context. What IS measurable from the pinned
snapshot per skill main-line: the four token categories (output / input /
cache_read / cache_write) and their cost, the rewrite subset (cache_write >
cache_read and > 50k — noting rewrites are the re-billing mechanism for
accumulated context, so these overlap, not partition), and `tool:Read`
frame COUNTS per turn. Filenames live only in the raw `~/.claude`
transcripts — recovering them is a qualitative, unpinned step against
mutable data (the profile's `session` labels give the transcript IDs to
open). If path-carrying tool frames would make this audit repeatable,
file that gap under specs/agentprof-instrumentation — don't build it here.

## Solution

Two phases. Phase 1 (measure): for each skill's main-line samples, report
the measurable splits — cost by token category (output / input /
cache_read / cache_write), the rewrite subset's cost, and a qualitative
list of `tool:Read` frames with the skill step that emitted them — plus a
per-session timeline for the 2–3 costliest skill-attributed sessions.
All numbers run against the frozen snapshot checked in at
`samples-2026-07-04-to-11.jsonl.gz` in this spec dir (gunzip and run
scripts against it; the matching pprof profile is
../drain-wake-cost/profile-2026-07-04-to-11.pb.gz). The command
`agentprof claude --since 2026-07-04T00:00:00Z` is provenance only — it
has no upper bound, so re-running it later pulls in newer activity and
does NOT reproduce these numbers. If a skill's week sample is too thin,
capture a fresh wider snapshot, check it in alongside, and label which
numbers come from which. Phase 2
(fix): apply the indicated restructuring per skill — the /parallel shape
(dispatch immediately, subagents hold the material, main context assembles
decisions only) is the target profile where the findings support it. The
known candidate for /breakdown, with a concrete routing rule (the token
categories alone can't arbitrate, since Read-heavy context also manifests
as cache_write rewrites): **if doctrine-violating `tool:Read` frames exist
at a delegable step — confirmed by opening the transcript — R2's targeted
skill-text fix wins, regardless of rewrite share; the drafter restructure
is pre-approved only when no such frames exist AND output_tokens +
cache_write dominate the skill's main-line cost.** The restructure:
delegate per-task file *drafting* to subagents that Write the task files
directly, where the main session pins every coupling decision (Status,
Depends-on, Touch, Group) AND authors every `Acceptance` command itself —
drafters produce Goal/Steps prose only, which is what makes cheap-tier
drafters safe.

## Requirements

- R1 **Findings doc.** `docs/orchestrator-share-findings.md` in this repo:
  for each of /breakdown, /build, /idea — (i) main-line cost split by token
  category, (ii) the rewrite subset's cost, (iii) main-line `tool:Read`
  frame counts per turn from the frozen snapshot, then for nonzero turns
  the filenames + emitting step recovered from the raw transcripts
  (qualitative, labeled as unpinned; explicitly NOT dollar figures),
  (iv) a keep/restructure verdict with one-paragraph rationale applying
  the Solution's routing rule. Every snapshot-derived number carries the
  command that produced it, runnable against the frozen
  `samples-2026-07-04-to-11.jsonl.gz` (custom jsonl scripts are fine —
  include them inline or as a checked-in script).
- R2 **Doctrine-violation check.** If transcript inspection (R1 iii) shows
  main-line Reads of files the skill's doctrine says to delegate, the
  findings name the files and the step, and the skill text gets a targeted
  fix at that step — not more general exhortation.
- R3 **Restructure where indicated.** For each skill whose verdict is
  "restructure", implement it. /breakdown's drafter restructure (as scoped
  in Solution: main session owns all coupling decisions and every
  Acceptance command; drafters write Goal/Steps prose only) is pre-approved
  only under the Solution's routing rule (no doctrine-violating Read frames
  AND output+cache_write dominance); confirmed violations route to R2.
  Other restructures go back through /critique first. Any skill-file
  change ships through the repo's mirror + plugin.json-bump gate.
- R4 **Regression hook.** The findings doc ends with the one-liner agentprof
  command + threshold that re-checks orchestrator share per skill, so the
  next weekly profile can spot regressions without re-deriving the method.
- R5 **Concrete outcome forced.** The audit may not close as a pure no-op:
  it ends with at least one of {a landed restructure, a targeted skill-text
  diff, or an explicit per-skill "already optimal" certification backed by
  the R1 token-category numbers showing the spend is intrinsic synthesis or
  user-paced interview time}.

## Out of scope

- /drain's hub cost (specs/drain-wake-cost owns it).
- /parallel (already at the target profile).
- Changing what these skills produce (spec format, task-file format,
  interview flow) — only *where* the tokens are spent producing it.
- agentprof feature work (it already carries tool frames and the needed
  metrics; if a genuine gap surfaces, file it under
  specs/agentprof-instrumentation instead).

## Acceptance criteria

- [ ] `test -f /Users/sjaconette/claude/docs/orchestrator-share-findings.md` with per-skill token-category splits, rewrite subset, tool:Read counts (+ transcript-recovered filenames for nonzero turns, labeled unpinned), and verdicts (R1)
- [ ] Every snapshot-derived number in the findings doc is accompanied by the command that produced it, runnable against the frozen `samples-2026-07-04-to-11.jsonl.gz` in this spec dir (R1)
- [ ] For each doctrine violation found, a corresponding skill-text diff exists at the violating step, or the findings state none were found (R2)
- [ ] Each "restructure" verdict has a landed implementation or an explicit deferral with reason; landed skill-file changes pass `bash /Users/sjaconette/claude/evals/lint-ultra-gate.sh` and `claude plugin validate .` with mirror + plugin.json bump (R3)
- [ ] Findings doc ends with the regression-check command and thresholds (R4)
- [ ] At least one concrete outcome exists per R5 (restructure landed, skill-text diff landed, or backed "already optimal" certification) — MANUAL confirm the certification is number-backed, not asserted (R5)
- [ ] MANUAL (deferred, needs post-change runs): next 7-day profile shows /breakdown orchestrator share materially below the 84% baseline, or the findings doc justified keeping it

## Open questions

- /idea's interview step is inherently main-line and user-paced (cache
  expiry between AskUserQuestion turns is user think-time, not design) —
  should its TTL-expiry rewrites be excluded from its share before judging?
  Decide in Phase 1 when the numbers are on the table.
- Is /build's 78% dominated by its small sample ($74 total)? If the week's
  sample is too thin per skill, widen to `--days 30` for Phase 1.
