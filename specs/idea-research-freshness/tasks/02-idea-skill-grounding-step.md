# Task 02: /idea's new grounding-check step 2, and the full renumbering sweep

Status: done
Depends on: none
Priority: P0
Budget: 12 turns
Spec: ../SPEC.md (requirements R2, R9)
Touch: .claude/skills/idea/SKILL.md

## Goal

`.claude/skills/idea/SKILL.md` gains a new step 2 (between today's step 1
scout and step 2 interview): when the idea's own framing signals a need
for external grounding (illustrative, not exhaustive, phrase patterns
like "best practices," "how do [vendor/tool] do this," "research X,"
"backed by research/blogs from ..."), run
`.claude/skills/idea/test-fixtures/research-freshness/check-freshness.sh`
against `docs/` for a topically-matching `Verified:` stamp within the
90-day window before dispatching anything: a fresh match is cited
directly (`docs/<path>:<line>`) with no research agents dispatched; a
stale or absent match dispatches research the existing way (factcheck vs.
deep-research per `.claude/rules/token-discipline.md`'s routing) and then
writes/refreshes the `Verified: <today>` stamp on the doc section the
findings land in. Inserting this step renumbers today's steps 2-6 to 3-7,
and every internal `step N` cross-reference elsewhere in the file — both
the space form ("step 3") and the hyphenated form ("post-step-3") — is
updated to match; none is left pointing at a pre-insertion number.

## Touch

Do not touch `antigravity/.agents/skills/idea/SKILL.md` — its own,
independently-numbered mirror is task 03. Do not touch
`.claude/skills/idea/test-fixtures/` — that's task 01 (this task only
_references_ `check-freshness.sh`'s path, doesn't create it; if task 01
hasn't landed yet, the path is still correct to write since it's fully
pinned in the spec).

## Steps

1. Read `.claude/skills/idea/SKILL.md` in full and find every `step
[0-9]` and `post-step-[0-9]` (or similar hyphenated) cross-reference —
   the spec's authoring-time count was ~12, including hyphenated
   references at (spec-authoring-time) lines 127, 130, 137 that a
   space-only search would miss. Re-derive this list fresh against the
   live file rather than trusting stale line numbers.
2. Insert the new step 2 (grounding-check), worded per Goal above,
   between today's steps 1 and 2. State the 90-day window, that
   `check-freshness.sh` (or equivalent logic) decides the fresh/stale/
   absent branching, and explicitly that the phrase-pattern triggers are
   "illustrative, not exhaustive."
3. Renumber every subsequent step (old 2→3, 3→4, 4→5, 5→6, 6→7) and
   update every cross-reference found in step 1 to match the new
   numbering — including the hyphenated `post-step-N` forms.
4. Run `bash evals/lint-ultra-gate.sh` — the new step must land before
   `## Ultra path`, not disturb the "active runtime profile" marker's
   ±3-line window.

## Acceptance

- [x] `grep -A5 "^## 2\." .claude/skills/idea/SKILL.md | grep -qi "90.day\|90 day"` (the new step 2 names the window) — PASS ("90-day freshness window" in step 2 body); evidence/02-idea-skill-grounding-step.md
- [x] `grep -c "check-freshness.sh\|equivalent logic" .claude/skills/idea/SKILL.md` → 1 or more — PASS, count=2; evidence/02-idea-skill-grounding-step.md
- [x] `grep -qi "illustrative, not exhaustive\|illustrative.*not exhaustive" .claude/skills/idea/SKILL.md` — PASS; evidence/02-idea-skill-grounding-step.md
- [x] `grep -n "step[ -][0-9]" .claude/skills/idea/SKILL.md` — manually verify each hit references the correct post-renumbering heading (no automatable single-command check; this is the per-reference consistency sweep from the spec's AC) — PASS, all 14 refs resolve under new 1-7 numbering; evidence/02-idea-skill-grounding-step.md
- [x] `bash evals/lint-ultra-gate.sh` exits 0 — PASS, exit 0; evidence/02-idea-skill-grounding-step.md
