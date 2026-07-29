# Design docs should preserve mechanism-first invariants

## Incident

A post-mortem session briefly framed repository architecture through prose-heavy metric claims:
`docs/design.md` treated this repo as mostly prose compared to enforcement tooling.
The claim did not match what the executable mechanisms and SKILL.md bodies already
captured, and that mismatch was corrected by the design correction pass.

## Lesson

When writing repo design documentation, preserve the mechanism-first source of truth:
- treat docs as explanation, not substitute evidence,
- verify claims against the executable definitions (skills, scripts, hooks, tests), and
- prioritize mechanism-backed metrics over intuition in assertions.

## Trigger

Use this lesson when the task is editing repository architecture/strategy docs.
