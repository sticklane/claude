# Task 01: Add browser-automation-handoffs rule

Status: pending
Depends on: none
Priority: P1
Budget: 8 turns
Spec: ../SPEC.md (requirements R4)
Touch: .claude/rules/browser-automation-handoffs.md

## Goal

A new rule file `.claude/rules/browser-automation-handoffs.md` exists,
stating as canonical doctrine that any claude-in-chrome-driven flow which
encounters a Google SSO/One-Tap login surface attempts at most ONE click
strategy against it before handing off to the human, rather than retrying
alternate strategies. The rule is written once so other claude-in-chrome
skills (this spec's `qa-sweep`, and eventually others) can cite it instead
of restating the behavior inline.

## Touch

Create exactly one new file: `.claude/rules/browser-automation-handoffs.md`.
Do not touch `.claude/skills/qa-sweep/` or any other rule file — a sibling
task creates the skill that cites this rule, and both tasks are safe to run
in parallel because this task's content is fully specified by the spec (no
shared undecided design with the sibling).

## Steps

1. Read 2-3 existing short rule files for house style — e.g.
   `.claude/rules/human-blockers.md` and `.claude/rules/concurrent-sessions.md`
   (title, one motivating paragraph with a citation to what evidence
   grounded it, then the concrete doctrine, in the "cite it, don't restate
   it" shape this repo's other rules use).
2. Write `.claude/rules/browser-automation-handoffs.md`:
   - Title and a short paragraph grounding the rule: four distinct click
     strategies were tried against a Google SSO/One-Tap chip in a real
     session before handing off to a human — wasted effort a fast
     detect-and-handoff rule would have avoided (this spec's Problem
     section / Research grounding has the exact evidence quote — reuse it
     or paraphrase it, citing it as task evidence).
   - State the doctrine: any claude-in-chrome-driven flow that detects a
     Google SSO/One-Tap login surface attempts at most ONE click strategy
     against it, then hands off to the human rather than retrying
     alternate strategies. Name the surface explicitly — the file must
     contain a case-insensitive match for "one-tap", "single sign-on", or
     "sso" (whichever reads most naturally in context; "one-tap" is likely
     the most natural given the evidence).
   - Keep it short (well under 100 lines) — this is a single, narrow
     behavioral rule, not a reference document.

## Acceptance

- [ ] `test -f .claude/rules/browser-automation-handoffs.md` → exists
- [ ] `grep -qi "one-tap\|single sign-on\|sso" .claude/rules/browser-automation-handoffs.md` → match found
- [ ] `git diff --stat` shows only `.claude/rules/browser-automation-handoffs.md` added — no other files touched
