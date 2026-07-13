Status: open
Priority: P2

## Problem

CLAUDE.md states two SKILL.md authoring conventions as musts:

> SKILL.md bodies stay well under 500 lines... heavy reference goes in a
> separate file, loaded on demand.

> Reference files over 100 lines open with a table of contents.

Neither is mechanically enforced — both rely on diligence, and diligence
has already failed repeatedly and measurably:

- `.claude/skills/drain/SKILL.md` is **517 lines** right now (verified
  `wc -l`, 2026-07-13) — over budget again. This is not the first time:
  `specs/work-exhaustion/tasks/05-shrink-drain-skill.md` did a one-time
  manual trim back to 499 lines (status: done, evidence citing the exact
  `wc -l` result), and the file has since crept back past 500 with no
  gate to catch the regression. Separately, real sessions have hit this
  ceiling live: one session went from 519 to 501 lines requiring a manual
  mid-session trim, noting the constraint had "recurred before"; another
  found the file sitting at exactly 500 with zero headroom; a third hit
  547 lines (47 over budget) and filed the fix as a human `decide` item
  rather than risk losing compaction-critical content by relocating prose
  ad hoc (SKILL.md bodies truncate on compaction; reference files do not —
  CLAUDE.md's authoring-conventions bullet).
- `.claude/skills/drain/reference.md` is **1595 lines** (verified `wc -l`)
  with no heading-style table of contents — its only navigation aid is a
  prose paragraph after the title (`Contents: When NOT to drain · Gen-1
  startup advisories · ...`), not a `## Table of contents` / `## Contents`
  heading. A session with no upfront map of the file ran 14 separate
  section-grep queries against it instead of one read, and two other
  sessions independently re-read large chunks mid-session for the same
  reason — token waste directly attributable to the missing TOC.
- The gap is not confined to drain: of this repo's 10 `.claude/skills/*/reference.md`
  files, 7 exceed the 100-line TOC threshold (factcheck 111, evals 119,
  prose-review 204, gate 198, workflow-author 250, fleet 190, autopilot
  159 — all verified `wc -l`, 2026-07-13) and **none** of the 10 has a
  heading matching `## Table of contents` or `## Contents` anywhere in the
  file (verified: `grep -rl` for both headings across all 10 returns zero
  hits). The convention is stated once in CLAUDE.md and followed nowhere.

## Solution

Add a standalone, model-free lint script under `evals/` — mirroring the
existing `evals/lint-ultra-gate.sh` pattern (bash, `set -u`, repo-root
resolved from `BASH_SOURCE`, a `FILES`/glob list, violations printed as
`file:line: reason`, non-zero exit on any violation, invoked directly
rather than wired into `evals/run.sh`) — that mechanically checks both
conventions across every `.claude/skills/*/SKILL.md` and
`.claude/skills/*/reference.md`. Bring the repo into compliance with it
(shrink `drain/SKILL.md`, add TOC headings to the 7 reference.md files
that need one) so the gate lands green, and reference the gate from
drain's own pre-merge checklist so a future generation that fattens a
SKILL.md or reference.md catches the regression mechanically instead of a
human hand-trimming it reactively weeks later.

## Research grounding

> "SKILL.md bodies stay well under 500 lines... heavy reference goes in a
> separate file, loaded on demand." — CLAUDE.md, Authoring conventions

> "Reference files over 100 lines open with a table of contents." —
> CLAUDE.md, Authoring conventions

> "this session handled ... matched how the earlier task handled this
> same constraint" — cited by the research sweep as evidence the drain
> SKILL.md overflow had already recurred before this session

> "SKILL.md files put execution-critical contracts in their first 30
> lines — skill bodies truncate when a session compacts; consulted docs
> do not." — CLAUDE.md, Authoring conventions (the reason relocating
> prose out of SKILL.md is not risk-free and needs a stated line budget
> rather than ad hoc trimming)

## Requirements

1. **New gate script `evals/lint-skill-size-gate.sh`.** Standalone,
   directly invocable (`bash evals/lint-skill-size-gate.sh`), matching
   `evals/lint-ultra-gate.sh`'s conventions: `set -u`, `ROOT` resolved
   from `BASH_SOURCE`, a discovery loop (glob or explicit list) over
   `.claude/skills/*/SKILL.md`, per-violation output as `path:count:
   reason`, a final `lint-skill-size-gate: OK` / `FAIL` line, exit 0 only
   if every file is compliant.
2. **SKILL.md line-budget check.** For every `.claude/skills/*/SKILL.md`,
   fail if `wc -l` exceeds 500 (the concrete threshold for CLAUDE.md's
   "well under 500 lines" — chosen because it is the number CLAUDE.md's
   own authoring-conventions bullet and every cited overflow session
   already measure against).
3. **reference.md TOC-presence check.** For every file matching
   `.claude/skills/*/reference.md` (glob; do not hardcode the list, so a
   new skill's reference.md is covered automatically) whose `wc -l`
   exceeds 100, fail unless the file contains a heading line matching
   (case-insensitive) `^## (Table of [Cc]ontents|Contents)\b` within the
   first 20 lines of the file. Files at or under 100 lines are exempt
   (matches CLAUDE.md's literal "over 100 lines" wording).
4. **Remediate `drain/SKILL.md` to ≤500 lines.** Same procedure as
   `specs/work-exhaustion/tasks/05-shrink-drain-skill.md`: move detail
   prose (not contract statements) into `drain/reference.md`, leave a
   one-line pointer, keep execution-critical contracts in the first 30
   lines, and verify no machine-checked token any other spec greps for
   (e.g. `agentprof:stage=`, `agentprof:role=` counts, `## Decisions`,
   `/handoff`) is lost — check with the same greps task 05 used before
   calling it done.
5. **Remediate `drain/reference.md` and the 6 other over-100-line
   reference.md files to carry a compliant TOC heading.** For
   `drain/reference.md`, promote its existing prose "Contents:" line into
   (or supplement it with) a `## Table of contents` heading listing the
   file's `## `-level sections, matching requirement 3's pattern. Do the
   same for `factcheck/reference.md`, `evals/reference.md`,
   `prose-review/reference.md`, `gate/reference.md`,
   `workflow-author/reference.md`, `fleet/reference.md`, and
   `autopilot/reference.md` (each currently over 100 lines with no
   qualifying heading — verified 2026-07-13).
6. **Wire the gate into drain's own pre-merge checklist.** Add a step to
   `.claude/skills/drain/reference.md`'s "Exit checklist" or "Push guard
   (canonical)" section (exact placement is an implementation decision)
   that runs `evals/lint-skill-size-gate.sh` whenever a generation's
   `Touch:` includes a `.claude/skills/*/SKILL.md` or
   `.claude/skills/*/reference.md` path, and treats a non-zero exit as a
   merge blocker for that task — the same mechanical role
   `lint-ultra-gate.sh` already plays for the ultra-path skills, but
   invoked conditionally rather than unconditionally since most drain
   tasks don't touch skill docs at all.
7. **Mirror obligations.** Requirements 4 and 6 change
   `.claude/skills/drain/SKILL.md` content, which is one of the four
   `drain`/`build`/`autopilot`/`evals` skills mirrored as *real content*
   (not a symlink) into `codex/.agents/skills/drain/SKILL.md` — that file
   must get the matching update. `drain/SKILL.md` and `drain/reference.md`
   changes also need the antigravity leg: drain is a human-only-launch
   skill mirrored as a workflow (`antigravity/.agents/workflows/drain.md`,
   currently 1056 lines), per the port-chain rule in CLAUDE.md's
   authoring-conventions bullet — mirror the procedural content there too
   (`.claude/rules/mirror-procedure-discipline.md` governs how: same
   steps, same order, same stated conditions, not a rewrite). Bump
   `.claude-plugin/plugin.json`'s `version` (currently `0.8.63`) one
   patch level per CLAUDE.md's "Bump version... whenever skill behavior
   changes."
8. `evals/lint-skill-size-gate.sh` itself lives under `evals/` and is a
   general-purpose lint script, not SKILL.md content — it does not itself
   need antigravity/codex mirroring (per the task framing precedent:
   "a general-purpose lint script added elsewhere in the repo... doesn't
   need mirroring itself").

## Out of scope

- Enforcing either convention on non-SKILL.md, non-reference.md docs
  (README.md, docs/*.md, agent definitions) — those are `/prose-review`'s
  charter, not this gate's.
- Auto-summarization or automatic prose-shrinking tooling. This spec adds
  detection plus one round of manual remediation; a worker (or human)
  still decides what to move and how to phrase the TOC.
- Wiring the new gate into `evals/run.sh` — like `lint-ultra-gate.sh`, it
  stays a standalone, directly-invoked script (model-free checks don't
  belong in the model-session evalset).
- Enforcing the line budget or TOC rule inside `antigravity/` or `codex/`
  mirror files themselves — the convention as stated in CLAUDE.md governs
  `.claude/skills/`; the mirrors get the same prose ported per
  `mirror-procedure-discipline.md`, not a separate size gate of their own.

## Acceptance criteria

- `test -x evals/lint-skill-size-gate.sh || test -f evals/lint-skill-size-gate.sh`
  → file exists.
- `bash evals/lint-skill-size-gate.sh; echo "exit:$?"` → `exit:0` (must be
  green after requirements 4–5 land; currently would exit non-zero since
  `drain/SKILL.md` is 517 lines and 7 reference.md files lack a TOC
  heading — anchored per docs/memory/anchored-acceptance-criteria.md).
- `wc -l < .claude/skills/drain/SKILL.md` → a number ≤ 500 (currently 517;
  must drop after requirement 4).
- `grep -qiE '^## (Table of [Cc]ontents|Contents)\b' .claude/skills/drain/reference.md`
  → match (currently absent — confirmed via `grep -c` returning 0 against
  the file's current content, 2026-07-13).
- `for f in factcheck evals prose-review gate workflow-author fleet autopilot; do grep -qiE '^## (Table of [Cc]ontents|Contents)\b' .claude/skills/$f/reference.md || echo "MISSING:$f"; done`
  → empty output (no `MISSING:` lines).
- `diff <(git show HEAD~1:codex/.agents/skills/drain/SKILL.md 2>/dev/null) codex/.agents/skills/drain/SKILL.md`
  → non-empty diff (confirms the codex mirror was actually updated, not
  skipped) — run against the commit that lands requirement 7.
- `grep -n '"version"' .claude-plugin/plugin.json` → value differs from
  `0.8.63` (the version at spec authoring time).
- `grep -q "lint-skill-size-gate" .claude/skills/drain/reference.md` →
  match (the gate is referenced from drain's own checklist per
  requirement 6).
- MANUAL: confirm the antigravity workflow mirror
  (`antigravity/.agents/workflows/drain.md`) reads as procedurally
  equivalent to the updated `drain/SKILL.md` + `drain/reference.md` pair
  per `.claude/rules/mirror-procedure-discipline.md`'s load-bearing vs.
  incidental classification — a live cross-reference sweep per
  `.claude/rules/mirror-verification.md`, not grep-checkable.

## Open questions

- Requirement 6 leaves the exact hook point in drain's checklist
  (Push guard vs. Exit checklist) to implementation — worth confirming
  which section a human wants it in before breakdown, or leave it as an
  implementation judgment call.
- Should the 500-line SKILL.md budget apply uniformly to every skill, or
  should some skills (e.g. drain, which coordinates the most machine-read
  state) get a documented higher ceiling instead of perpetually fighting
  the same limit? This spec assumes the uniform 500 CLAUDE.md already
  states; a human may want to revisit the number itself rather than keep
  re-enforcing it.
