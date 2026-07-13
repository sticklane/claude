# Proposed global `~/.claude/CLAUDE.md` one-liner

**MANUAL (attended): for Steven to apply.** `~/.claude/CLAUDE.md` is
user-private and outside this repo, so this artifact only *proposes* the
text — applying it is a manual step, not something this task (or any
unattended worker) does.

## Why

This repo's `.claude/rules/` load only when a session runs inside the
toolkit repo. The measured freehand-drain spend is cross-repo:
~$1,406/week of unstructured orchestration ran under `(no skill)` — about
5× the attributed `skill:drain` cost — without any of the skill's
window/baton/verdict structure (specs/drain-wake-cost/EVIDENCE.md). The
in-repo doctrine block in `.claude/rules/token-discipline.md` covers
toolkit-repo sessions; a one-liner in the global CLAUDE.md carries the same
recommendation into every other repo's sessions.

## Proposed line

> When a request is drain-shaped ("drain the …", "work through the remaining
> tasks in specs/…"), recommend launching `/drain` rather than improvising an
> unstructured dispatch loop — its window/baton/verdict machinery is what keeps
> the loop cheap and safe. `/drain` is human-gated: recommend it, never launch
> it automatically.

## Placement

Put it under a delegation/orchestration heading near the other "when to
reach for a skill / delegate" guidance in `~/.claude/CLAUDE.md`, so it sits
with the token-discipline and delegation notes rather than in an unrelated
section.
