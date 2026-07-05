# Task 05: antigravity mirror + plugin bump + closing gates

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Priority values run P0 (highest) through P3; the header is optional — absent means P2. -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers, in every task file — and ## Progress / ## Deferred questions are drain-written sections (single writer, main checkout): workers report that content, never write it. -->

Status: done
Depends on: 02, 03, 04
Priority: P1
Budget: 12 turns
Spec: ../SPEC.md (requirement R10)
Touch: antigravity/, .claude-plugin/plugin.json

## Goal

Every skill file changed by tasks 02–04 is byte-mirrored into the
antigravity port (drain SKILL.md + reference.md, build SKILL.md,
autopilot SKILL.md, onboard SKILL.md — at their existing antigravity
paths; the new rules file mirrors per the port's convention for rules,
matching how existing rules are represented there — inspect before
copying), and `.claude-plugin/plugin.json` `version` is bumped once for
the whole spec. Full gate suite green at the end. Note: the spec's
MANUAL-PENDING e2e criterion is human-run and explicitly NOT this
task's (or any worker's) gate.

## Touch

Only `antigravity/` and `.claude-plugin/plugin.json`. Do NOT re-edit the
source skill files — if a mirror diff reveals a source problem, report
it as Discovered, don't fix it here.

## Steps

1. Diff each changed source skill file against its antigravity
   counterpart; copy source → mirror (byte-identical for files the port
   mirrors verbatim; see docs/memory/workboard-mirror-verbatim.md).
2. Determine how the port represents `.claude/rules/` files and mirror
   the new rule accordingly.
3. Bump plugin.json version once.
4. Full gate suite; commit.

## Acceptance

- [ ] For each changed skill file F: `diff .claude/skills/<F> antigravity/.agents/skills/<F>` → no output (byte-mirrored) — SUPERSEDED by ## Answers (paraphrased-port convention); see the 7 substitute checks there, all PASS.
- [x] `git diff main -- .claude-plugin/plugin.json | grep -c '"version"'` → 2 — ran: output `2` (0.8.8 → 0.8.9).
- [x] `for t in tests/test_*.sh; do bash "$t" || exit 1; done && ./bin/check-agent-model-pins && ./evals/runner-selftest.sh && ./specs/status.sh && claude plugin validate . && bash evals/lint-ultra-gate.sh` → exit 0 — ran: all suites pass, `claude plugin validate .` → "Validation passed", `lint-ultra-gate: OK`, exit 0.

## Deferred questions

- [2026-07-05 /drain] Worker verdict DEFERRED. Acceptance criterion 1 demands
  a byte-identical `diff` for drain SKILL.md + reference.md, build SKILL.md,
  autopilot SKILL.md, and onboard SKILL.md against antigravity paths. The
  worker verified this contradicts the repo's own documented convention:
  drain/build/autopilot are `disable-model-invocation: true` ("human-only")
  skills that per CLAUDE.md's taxonomy mirror to hand-paraphrased combined
  files at `antigravity/.agents/workflows/{drain,build,autopilot}.md` (no
  frontmatter/`$ARGUMENTS`, different terminology throughout; drain's
  reference.md has no separate mirror, folded into `workflows/drain.md`).
  `onboard/SKILL.md` does have a matching antigravity path but its mirror is
  likewise hand-paraphrased (CLAUDE.md→AGENTS.md, reworded steps), not
  byte-identical. `docs/memory/workboard-mirror-verbatim.md` states only
  workboard's two `.py` files are byte-for-byte across trees; prose-skill
  mirrors are documented as paraphrased ports requiring hand edits — the
  opposite of what criterion 1 demands.

  Does R10/task 05 mean to (a) override the established paraphrased-port
  convention and byte-copy these files into new/existing antigravity paths
  (destroying the existing Antigravity-adapted wording), or (b) keep the
  paraphrased-port convention and hand-update the existing `workflows/*.md`
  + `onboard/SKILL.md` to reflect tasks 02–04's new content in Antigravity's
  voice — in which case criterion 1's literal `diff → no output` command
  needs a human-approved substitute check (e.g., a content-coverage check
  rather than a byte diff)?

## Answers

- [2026-07-05 /drain] (b) — keep the established paraphrased-port
  convention. Hand-update `antigravity/.agents/workflows/drain.md`,
  `workflows/build.md`, `workflows/autopilot.md`, and
  `.agents/skills/onboard/SKILL.md` to reflect tasks 02–04's new content in
  Antigravity's own voice (its own terminology for the Task-tool-free
  orchestration mechanism, no `$ARGUMENTS`/frontmatter, etc.) — do not
  byte-copy the Claude source over these files.

  This supersedes criterion 1's literal byte-diff check (drain, the task
  file's single writer, is authorizing this replacement under this
  Answer). Substitute criterion 1 with these content-coverage checks —
  `DRAIN-OWNER` and `Run-token` are the coordination protocol's own file
  and field names (DRAIN-OWNER.md, DRAIN-BATON.md), not English prose, so
  they are runtime-agnostic identifiers that must survive verbatim in the
  Antigravity port even though the surrounding explanation is paraphrased:

  - [x] `grep -c "DRAIN-OWNER" antigravity/.agents/workflows/drain.md` → ran: `4` (≥ 1, PASS).
  - [x] `grep -c "Run-token" antigravity/.agents/workflows/drain.md` → ran: `6` (≥ 1, PASS).
  - [x] `grep -ciE "compare-and-swap|exact-match" antigravity/.agents/workflows/drain.md` → ran: `3` (≥ 1, PASS).
  - [x] `grep -c "path-scoped" antigravity/.agents/workflows/drain.md` → ran: `8` (≥ 1, PASS).
  - [x] `workflows/build.md` and `workflows/autopilot.md` each gain content
        conveying the startup session-sweep concept task 03 added (in
        Antigravity's own terms for enumerating other live sessions — it
        will not literally say `claude agents --json`, that's a Claude
        Code CLI command with no Antigravity equivalent); worker picks and
        runs a concrete grep proving the concept landed in each file
        (e.g. on a phrase it authors, such as "session sweep" or
        "live session"), and records the exact command + result as
        evidence — same evidentiary bar as every other criterion.
        Self-authored check: `grep -ci "session sweep\|live session"
        antigravity/.agents/workflows/build.md` → `1`; same command
        against `autopilot.md` → `3`. Both ≥ 1, PASS.
  - [x] `workflows/build.md` gains content conveying the owner-liveness
        warn-before-edit concept (citing, not restating, the liveness
        definition) — worker picks and runs a concrete grep proving it
        landed, records command + result as evidence.
        Self-authored check: `grep -ci "owner lease\|DRAIN-OWNER\|liveness"
        antigravity/.agents/workflows/build.md` → `2` (≥ 1, PASS) — the
        "Owner warning" clause citing the drain workflow's Owner lease
        liveness definition.
  - [x] `.agents/skills/onboard/SKILL.md` gains the optional
        concurrent-sessions pre-flight bullet in Antigravity's voice —
        `grep -ci "concurrent.session" antigravity/.agents/skills/onboard/SKILL.md` → ran: `3` (≥ 1, PASS).
  - [x] The new `.claude/rules/concurrent-sessions.md` rule mirrors per
        whatever convention the port already uses for `.claude/rules/`
        files (inspect before copying, per the Goal's original
        instruction — unchanged by this Answer).
        Inspected: `antigravity/README.md` states the port's convention —
        `.claude/rules/*.md` files fold into `AGENTS.md` as always-on
        sections (no separate rules dir; confirmed no `antigravity/**rules**`
        path exists and the three pre-existing rules already appear as
        AGENTS.md `##` sections). Added a paraphrased "## Concurrent
        sessions" section to `antigravity/AGENTS.md` following that
        pattern. Check: `grep -ci "concurrent session" antigravity/AGENTS.md`
        → `1` (≥ 1, PASS).

  All other Acceptance criteria (plugin.json version bump, full gate
  suite) are unchanged.
