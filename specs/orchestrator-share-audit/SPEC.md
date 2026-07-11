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

## Solution

Two phases. Phase 1 (measure): drill into the samples with agentprof's
existing dimensions — tool frames, per-call cache_read/cache_write/input
splits, and per-session timelines for skill-attributed sessions — and write
a short findings doc attributing each skill's main-line spend to (a) file
Reads the doctrine forbids, (b) legitimate synthesis output, (c) cache
rewrites, (d) accumulated conversation. Phase 2 (fix): apply the indicated
restructuring per skill — the /parallel shape (dispatch immediately,
subagents hold the material, main context assembles decisions only) is the
target profile where the findings support it. The known candidate if (a) or
(d) dominates for /breakdown: delegate per-task file *drafting* to pinned
cheap-tier subagents that Write the task files directly, with the main
session reviewing only the dependency map.

## Requirements

- R1 **Findings doc.** `docs/orchestrator-share-findings.md` in this repo:
  for each of /breakdown, /build, /idea, the main-line spend attributed
  across (a)–(d) above, with the analysis commands used (reproducible
  against a fresh `agentprof claude -o samples.jsonl` dump), and a
  keep/restructure verdict per skill with one-paragraph rationale.
- R2 **Doctrine-violation check.** If (a) is nonzero for any skill, the
  findings name the specific transcript evidence (which files got Read into
  the main session and at which step), and the skill text gets a targeted
  fix at that step — not more general exhortation.
- R3 **Restructure where indicated.** For each skill whose verdict is
  "restructure", implement it. /breakdown's candidate restructure (per-task
  drafter subagents that Write files directly; main session pins Status/
  Depends-on/Touch and reviews the map) is pre-approved if the findings
  point at drafting cost; other restructures go back through /critique
  first.
- R4 **Regression hook.** The findings doc ends with the one-liner agentprof
  command + threshold that re-checks orchestrator share per skill, so the
  next weekly profile can spot regressions without re-deriving the method.

## Out of scope

- /drain's hub cost (specs/drain-wake-cost owns it).
- /parallel (already at the target profile).
- Changing what these skills produce (spec format, task-file format,
  interview flow) — only *where* the tokens are spent producing it.
- agentprof feature work (it already carries tool frames and the needed
  metrics; if a genuine gap surfaces, file it under
  specs/agentprof-instrumentation instead).

## Acceptance criteria

- [ ] `test -f /Users/sjaconette/claude/docs/orchestrator-share-findings.md` with per-skill (a)–(d) attribution and verdicts (R1)
- [ ] Every analysis number in the findings doc is accompanied by the command that produced it (R1)
- [ ] For each doctrine violation found, a corresponding skill-text diff exists at the violating step, or the findings state none were found (R2)
- [ ] Each "restructure" verdict has a landed implementation or an explicit deferral with reason (R3)
- [ ] Findings doc ends with the regression-check command and thresholds (R4)
- [ ] MANUAL (deferred, needs post-change runs): next 7-day profile shows /breakdown orchestrator share materially below the 84% baseline, or the findings doc justified keeping it

## Open questions

- /idea's interview step is inherently main-line and user-paced (cache
  expiry between AskUserQuestion turns is user think-time, not design) —
  should its TTL-expiry rewrites be excluded from its share before judging?
  Decide in Phase 1 when the numbers are on the table.
- Is /build's 78% dominated by its small sample ($74 total)? If the week's
  sample is too thin per skill, widen to `--days 30` for Phase 1.
