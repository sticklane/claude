# Task 05: antigravity mirror + plugin bump + closing gates

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Priority values run P0 (highest) through P3; the header is optional — absent means P2. -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers, in every task file — and ## Progress / ## Deferred questions are drain-written sections (single writer, main checkout): workers report that content, never write it. -->

Status: deferred
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

- [ ] For each changed skill file F: `diff .claude/skills/<F> antigravity/.agents/skills/<F>` → no output (byte-mirrored)
- [ ] `git diff main -- .claude-plugin/plugin.json | grep -c '"version"'` → 2 (old + new line)
- [ ] `for t in tests/test_*.sh; do bash "$t" || exit 1; done && ./bin/check-agent-model-pins && ./evals/runner-selftest.sh && ./specs/status.sh && claude plugin validate . && bash evals/lint-ultra-gate.sh` → exit 0

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
