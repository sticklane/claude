# Verification: 01-drain-skill-stub-intake

Verdict: PASS

## Per-criterion

1. `grep -qi "stub intake" .claude/skills/drain/SKILL.md`
   Result: PASS (exit 0). Section header at line 499: `## Stub intake (fires
at the exhaustion trigger, after critique intake, before 3b)`.

2. `grep -qi "promoted this run" .claude/skills/drain/SKILL.md`
   Result: PASS (exit 0). Exit checklist item 6 (line ~677): "**Promoted
   this run** — every stub stub intake acted on: ...". Count text at line
   650: "the final message is a fixed **seven-section checklist**" — matches
   the required bump from six to seven, and the checklist below it lists
   items 1-7.

3. `rg -Uqi "only a human (promotes|edits)|only a human \(or|Promotion is
manual|promoted manually|only a human\s+(promotes|edits)" \
.claude/skills/drain/SKILL.md`
   Result: PASS — exit code 1 (no matches), as required.

4. `grep -n "reason 1" .claude/skills/drain/SKILL.md`
   Result: PASS — no output (no "reason 1" string remains anywhere in the
   file, case-sensitive or otherwise per `grep -ni` re-check). Both former
   "reason 1" draft-gate citations now read "reason 4" (lines 391, 496,
   528: `docs/human-gates.md reason 4`).

5. `grep -qi "adversarial" docs/human-gates.md`
   Result: PASS (exit 0, match in reason 4's woven text: "an **adversarial
   critic gate** as the judgment layer").
   Disable-model-invocation rationale preserved verbatim-in-substance
   (docs/human-gates.md lines 34-40): "A hard mechanism beats a soft rule
   where injection could escalate. Unattended workers read unvetted repo
   content. The untrusted-data rule says injected instructions carry no
   authority — but a rule is prose. `disable-model-invocation` removes
   gated skills from the model's context entirely (and blocks scheduled
   firing), so injected text can never transitively become a fleet of
   launched workers. 'Shouldn't' becomes 'can't' exactly where escalation
   would be catastrophic." This sentence is untouched; the draft-gate
   relocation (hard screen + re-authored Goal + adversarial critic gate;
   exit-checklist audit; `Demoted:` line) is woven into the same numbered
   reason immediately after it (lines 41-60), not appended as a new reason
   or replacing the launch rationale.

6. `bash evals/lint-ultra-gate.sh`
   Result: PASS — "lint-ultra-gate: OK — all ultra mentions gated in 4
   files", exit 0.

## Manual checks against the Goal

- **Section placement/evaluation order**: `## Stub intake` (line 499) sits
  directly after `## Critique intake` (line 454) and before `## 3b.
Auto-breakdown` (line 559) — confirmed via `grep -n "^## "` over the
  whole file. Its opening line states the trigger explicitly: "fires at
  the exhaustion trigger, after critique intake, before 3b's
  auto-breakdown loop-back". Section carries the assess→gate→act contract
  and a pointer: "The full pipeline (regex list, rubric, act rules) lives
  in [reference.md](reference.md), the detail home; SKILL.md carries this
  contract and pointer." It cites `Stub-intake-failed:` (line 510) and
  `.claude/skills/drain/screen-stub.sh` (line 513/521) by name, explicitly
  noting "task 02 owns reference.md and the screen script ... do not edit
  them." `git status --porcelain` and `git diff --stat` confirm
  `.claude/skills/drain/reference.md` and `screen-stub.sh` are untouched
  (reference.md unchanged; screen-stub.sh does not exist in this
  worktree, consistent with task 02 not yet run).

- **R7 statement revisions**: inventory step (lines 61-79) now reads
  "drain's **stub intake** ... promotes actionable ones `draft` →
  `pending` through a deterministic screen plus an adversarial gate, and a
  human audits every promotion via the exit checklist" — no "only a human
  promotes" language remains. Discoveries paragraph (~line 384-392) now
  reads "stub intake ... later assesses each and promotes `draft` →
  `pending` only after re-authoring the quoted Goal in neutral words and
  passing the adversarial gate" with citation "docs/human-gates.md reason
  4, cited not restated" — corrected from the former reason-1 citation.
  Critique-intake passage (lines 493-497) now reads "Draft TASK stubs are
  **not** critique intake — they are handled by **stub intake** (the next
  branch below)" — a pointer, not a standalone "not intake" statement.

- **human-gates.md weave**: confirmed above under criterion 5 — the
  launch rationale is preserved and the relocation content (hard screen,
  Goal re-authoring, adversarial critic gate mirroring `Breakdown-ready:`,
  exit-checklist audit, `Demoted:` line) is woven into the same reason,
  not replacing or duplicating as a sixth reason. `## The five reasons`
  header (line 10) still says "five" — count unchanged, consistent with
  weaving in place rather than adding a reason.

- **Scope**: `git diff --stat 598e7835ffb30bdf3e3fd328fed36f4b97fdb381 --
. ':!specs'` shows only:

  ```
  .claude/skills/drain/SKILL.md | 105 +++++++++++++++++++++++++++++++++++-------
  docs/human-gates.md           |  21 ++++++++-
  ```

  `git diff --stat ... -- specs` shows only the task file itself (14 lines
  added). `git status --porcelain` confirms no other tracked/untracked
  changes. `.claude/skills/drain/reference.md`, `screen-stub.sh`,
  `antigravity/`, and `.claude-plugin/` are all untouched.

- **Task-file append-only check**: `git diff
598e7835ffb30bdf3e3fd328fed36f4b97fdb381 -- specs/draft-auto-promotion/
tasks/01-drain-skill-stub-intake.md` shows only a 14-line addition: the
  `<!-- PLAN ... -->` comment block inserted after the header fields.
  Goal/Steps/Touch/Acceptance text is byte-identical to the base. The
  `Status:` line is unchanged (`in-progress`), and no acceptance
  checkboxes are ticked, no evidence-citation lines were added by the
  worker. This is allowed by the append-only contract (plan block may be
  added) but is a process gap worth flagging below.

## Findings (not acceptance failures)

- **Bookkeeping gap**: the task file's `Status:` remains `in-progress` and
  none of the 6 acceptance checkboxes are ticked, despite all 6 acceptance
  commands passing and the manual Goal checks confirming faithful
  implementation. The worker did not update Status or evidence lines per
  the task file's own append-only contract for workers. This does not
  affect the technical PASS verdict on the acceptance criteria themselves,
  but the task file does not yet reflect completion.
- No scope creep detected; no test-file or acceptance-criteria tampering
  detected (the acceptance section text is byte-identical to base).
