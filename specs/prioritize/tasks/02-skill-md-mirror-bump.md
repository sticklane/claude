# Task 02: /prioritize SKILL.md + antigravity mirror + plugin bump

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Priority values run P0 (highest) through P3; the header is optional — absent means P2. -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers, in every task file — and ## Progress / ## Deferred questions are drain-written sections (single writer, main checkout): workers report that content, never write it. -->

Status: done
Depends on: 01
Priority: P2
Budget: 12 turns
Spec: ../SPEC.md (requirements R3–R9)
Touch: .claude/skills/prioritize/SKILL.md, .claude/skills/list-specs/SKILL.md, antigravity/.agents/skills/prioritize/prioritize_scan.py, antigravity/.agents/skills/prioritize/test_prioritize_scan.py, antigravity/.agents/workflows/prioritize.md, .claude-plugin/plugin.json

## Goal

`.claude/skills/prioritize/SKILL.md` exists with
`disable-model-invocation: true`, a description that distinguishes
/prioritize (reorders `Priority:` headers) from /list-specs (reports the
next pipeline command, named as the alternative), and a body implementing
R3–R7: run `prioritize_scan.py`, present its table, ask exactly one
free-form question (R3's wording), validate replies per R4, edit
`Priority:` headers per R5, commit per R6, exit cleanly on "none" per R7.
The skill is mirrored into antigravity (script dir + a workflow, since it
is human-only) and `plugin.json`'s version is bumped.

## Touch

`list-specs/SKILL.md` is in Touch only for R9's reciprocal check — its
description ALREADY names /prioritize ("For reordering work … use
/prioritize instead"), so expect a no-op there; edit only if that sentence
is missing. Do NOT touch `.claude/skills/prioritize/prioritize_scan.py` or
its test (task 01 owns them; mirror copies are byte-copies into
`antigravity/`). Do NOT touch `.claude-plugin/plugin.json` beyond the
version bump.

## Steps

1. Read `../SPEC.md` R3–R9 and `.claude/skills/list-specs/SKILL.md` as the
   style model. Note CLAUDE.md authoring conventions: contracts in the
   first 30 lines; trigger phrases not required (human-only skill);
   `Next stage:` line required.
2. Write `.claude/skills/prioritize/SKILL.md`:
   - frontmatter: `disable-model-invocation: true`; description per R9
     (reorders `Priority:` headers, names /list-specs as the
     report-only alternative).
   - body: run `python3 .claude/skills/prioritize/prioritize_scan.py`
     (resolve the path via the skill's base directory the way other
     script-bearing skills do); if it prints "nothing to reprioritize",
     stop. Otherwise show the table and ask R3's single free-form
     question verbatim (explicitly NOT AskUserQuestion). Apply R4
     validation (Ref must match a table row; target must normalize to
     P0–P3; anything else listed back as "not applied: <reason>",
     never guessed). Apply R5 edit rules (replace `Priority:` in place;
     else insert below `Status:`; else first header line above the first
     heading; touch no other line). Commit per R6's exact message shape
     when ≥1 change applied; no commit on "none"/all-invalid (R7).
   - close with `Next stage: none — the human decides what to /build or
     /drain next`.
3. Verify R9's reciprocal sentence in
   `.claude/skills/list-specs/SKILL.md`'s description; edit only if
   absent.
4. Mirror per convention (workboard-cli task 04 is the model): byte-copy
   `prioritize_scan.py` + `test_prioritize_scan.py` to
   `antigravity/.agents/skills/prioritize/`, and port the SKILL.md prose
   as the workflow `antigravity/.agents/workflows/prioritize.md`
   (human-only skills become workflows — `build.md`/`drain.md` are the
   shape).
5. Bump `version` (patch) in `.claude-plugin/plugin.json`.

## Acceptance

- [x] `grep -q 'disable-model-invocation: true' .claude/skills/prioritize/SKILL.md` → exit 0 — verifier PASS (evidence/02-skill-md-mirror-bump.md)
- [x] `grep -q 'list-specs' .claude/skills/prioritize/SKILL.md` → exit 0 (R9 disambiguation present) — verifier PASS
- [x] `grep -qF 'Next stage: none' .claude/skills/prioritize/SKILL.md` → exit 0 — verifier PASS
- [x] `grep -q 'prioritize' .claude/skills/list-specs/SKILL.md` → exit 0 (R9 reciprocal) — verifier PASS (list-specs untouched; sentence pre-existed)
- [x] `diff .claude/skills/prioritize/prioritize_scan.py antigravity/.agents/skills/prioritize/prioritize_scan.py && diff .claude/skills/prioritize/test_prioritize_scan.py antigravity/.agents/skills/prioritize/test_prioritize_scan.py` → identical — verifier PASS (byte-identical)
- [x] `test -f antigravity/.agents/workflows/prioritize.md` → exit 0 — verifier PASS
- [x] `git diff HEAD~1 -- .claude-plugin/plugin.json | grep -q '"version"'` → version bumped in this task's commit range (equivalently: plugin.json version > 0.8.12) — verifier PASS (0.8.13 > 0.8.12; only version line changed)
- [x] `python3 -m pytest .claude/skills/prioritize/ .claude/skills/workboard/ .claude/skills/list-specs/ -q` → all pass (this repo has no top-level scripts/check.sh; these suites are the relevant gates) — verifier PASS (100 passed)
- [x] Fixture run, apply one change (spec bullet 4): headless `claude -p "/prioritize …reply: make alpha/02-fix-cache.md P0"` in a fixture repo (skill copied in with `disable-model-invocation` removed in the COPY only) → exactly one commit `chore: reprioritize 1 task(s) across 1 spec(s) per interview` touching only that file; `Priority: P0` inserted below `Status:` — PASS (evidence/02-interactive-e2e.md, Run A)
- [x] Fixture run, invalid Ref + valid change (spec bullet 5): reply `make alpha/99-typo.md P1, and make beta/01-docs-pass.md P1` → invalid Ref reported `not applied`, valid change still applied in place (P3→P1) and committed alone — PASS (evidence/02-interactive-e2e.md, Run B)
- [x] Fixture run, reply "none" (spec bullet 6): R3 question asked verbatim, no edits, no commit, clean tree — PASS (evidence/02-interactive-e2e.md, Run C)
- [x] Real repo, production flag intact (spec bullet 7, read-only half): user-typed `/prioritize` triggers despite `disable-model-invocation: true`, renders the live table, exits on "none" with HEAD unchanged; the commit-producing half completes the first time a human genuinely reprioritizes (automation must not invent an ordering) — PASS (evidence/02-interactive-e2e.md, Run D)
