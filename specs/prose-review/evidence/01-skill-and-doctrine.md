# Verification: 01-skill-and-doctrine

Verdict: PASS

## Criterion 1 — grep anchors in reference.md

Command:
```
grep -qi 'DeepMind' .claude/skills/prose-review/reference.md && grep -qi 'right now' .claude/skills/prose-review/reference.md && grep -qi 'stumble' .claude/skills/prose-review/reference.md
```
Output: all three grep -q calls succeeded (exit 0 each) — printed
"DeepMind hit", "right now hit", "stumble hit". PASS.

## Criterion 2 — vendor citation count

Command:
```
grep -c 'developers.google.com/style\|diataxis.fr' .claude/skills/prose-review/reference.md
```
Output: `4` (≥ 2 required). PASS.

## Criterion 3 — CLAUDE.md pointer

Command:
```
grep -q 'prose-review' CLAUDE.md
```
Output: exit 0. Actual line (CLAUDE.md:32-35):
```
- Human-facing prose (README.md, AGENTS.md, docs/*.md) is `/prose-review`'s
  charter: review edits to it with `/prose-review`, and load that skill's
  doctrine before drafting such a doc. Machine-parsed prose (task files,
  specs/, SKILL.md bodies) is out of its scope.
```
PASS.

## Criterion 4 — SKILL.md line count

Command:
```
wc -l < .claude/skills/prose-review/SKILL.md
```
Output: `84` (< 500 required). PASS.

## Criterion 5 (MANUAL) — nine items with vendor quotes; --fix rules; reader-test skips diffs/pasted text

**Nine rubric items (reference.md:14-90), each with vendor + quote:**
1. List/bullet overuse — Anthropic "DO NOT use ordered lists ... unless
   ... discrete items"; OpenAI "plain paragraphs as the default format";
   Amazon "we don't do PowerPoint ... narratively structured six-page
   memos". **Carve-out present** (reference.md:29-38): "does NOT fire on
   structured technical documents... A spec's `## Requirements` /
   `## Acceptance criteria` sections, API references... are NOT 'list
   overuse'... per Anthropic's own carve-out."
2. Excessive hedging — OpenAI "excessive hedging ... disclaimers ...
   reminders that it's an AI".
3. Sycophancy — Anthropic (named problem); OpenAI "not ... flatter them
   or agree with them all the time".
4. Over-formatting — Anthropic "avoids over-formatting with bold
   emphasis, headers, lists".
5. Purple prose/clichéd filler — OpenAI "purple prose, hyperbole,
   self-aggrandizing, and clichéd phrases".
6. Stock acknowledgments — OpenAI "stock acknowledgments like 'Got it'".
7. Repetitive phrasing — DeepSeek (R1 README/paper); Mistral
   frequency/presence_penalty; Amazon "verbosity hacking".
8. Vague/blurry language — Mistral "avoid blurry words like 'things',
   'stuff' ... state exactly what you mean".
9. Self-celebratory language — Anthropic "fact-based progress reports
   rather than self-celebratory updates".

DeepMind carve-out (reference.md:86-90): "DeepMind contributes no rubric
item... recorded here as contributing nothing rather than silently
omitted or padded with an invented item." Matches R1 and Goal.

**--fix rules (R3/R4), SKILL.md:20-27, 66-73:**
- "The read-only report mode is model-invocable... `--fix` is human-typed
  only: never infer or add it from a vague request." (line 20-22)
- "A flag cannot distinguish a human-typed argument from a model-added
  one, so this is a behavioral rule, not a mechanism." (line 23-24)
- "`--fix` requires a file-path target — given a diff or pasted text it
  errors ('--fix needs a file path to write to') rather than guessing
  where the text lives." (line 68-70)
Matches R3 (read-only default, file-path-only, errors on non-file) and
R4 (human-typed only, behavioral not mechanical) exactly.

**Reader test skips diffs/pasted text (R6), reference.md:163-167 and
SKILL.md:47-51:**
- reference.md:150 "spawn ONE fresh-context agent (session tier, no
  prior context..."
- reference.md:165-167: "Review mode runs the reader test for
  orientation docs (README.md, AGENTS.md) by default and skips it for
  diffs and pasted text — a fragment has no cold-read context to test."
- SKILL.md:47-51: "Reader test — for orientation docs (README.md,
  AGENTS.md) by default... Skip it for diffs and pasted text."
Matches R6.

**R5 (Diátaxis quadrant table), reference.md:99-106:** table with four
rows binding Tutorial/How-to/Reference/Explanation to README.md/
AGENTS.md/docs/SKILL.md bodies, headed by "**What does the reader need
RIGHT NOW?** The answer picks the quadrant." Matches R5.

Criterion 5: PASS (all sub-points substantiated with quoted text from
the files).

## Touch scope / scope creep

Command: `git diff 1460c18e1354e7978e888d9ff0044e0be1e68f9b --stat`
```
 .claude/skills/prose-review/SKILL.md              |  84 +++++++++++
 .claude/skills/prose-review/reference.md          | 167 ++++++++++++++++++++++
 CLAUDE.md                                         |   4 +
 specs/prose-review/tasks/01-skill-and-doctrine.md |  20 +++
 4 files changed, 275 insertions(+)
```
Only files under Touch scope (`.claude/skills/prose-review/`, `CLAUDE.md`)
plus the task file itself changed. No scope creep. `git status
--porcelain` also shows no other tracked-file modifications and no
untracked files outside these paths.

## Append-only task-file check

Command:
```
git diff 1460c18e1354e7978e888d9ff0044e0be1e68f9b -- specs/prose-review/tasks/01-skill-and-doctrine.md
```
Output: the only change is an added `<!-- PLAN (delete at close-out) -->`
comment block (20 lines) between the header fields and `## Goal`. Status
line unchanged ("in-progress"), no acceptance checkboxes ticked, no
edits to Goal/Steps/Touch/Budget/acceptance-criterion text. Compliant
with the append-only contract (plan comment block is an allowed
worker edit).

## Minor observation (not a failing criterion)

reference.md is 167 lines (>100). Repo convention (CLAUDE.md: "Reference
files over 100 lines open with a table of contents.") calls for a
TOC. The file opens with a "Contents: ..." descriptive sentence
(reference.md:3-6) rather than a structured TOC list/links. This is a
convention observation, not one of the five task acceptance criteria,
so it does not affect the verdict, but is worth flagging for follow-up.

## Gate check

No `scripts/check.sh` exists at repo root for this toolkit repo (per
memory: "~/claude has no scripts/check.sh gate"). No repo-standard lint/
test gate was skipped; none applies to a two-markdown-file + one-CLAUDE.md-
bullet change.

## Overall verdict: PASS
