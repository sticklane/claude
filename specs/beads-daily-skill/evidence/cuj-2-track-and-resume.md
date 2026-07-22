# CUJ-2 — Track and resume

Two live runs, 2026-07-22.

## Scratch repo

```
bd create "implement the widget parser" -t task -p 1  → cuj1-90m
bd update cuj1-90m --claim; echo cuj1-90m > .beads/session-claims
# session tries to end with the claim open:
check.sh ← {"stop_hook_active": false, ...}
  bd-compliance: claimed issue(s) still open — close them before
  ending the session: cuj1-90m
  exit=2                                   (blocked, names the id)
bd close cuj1-90m --reason "parser done"; truncate session-claims
check.sh → exit=0                          (passes after close+unclaim)
# "new session" resume = a query, no handoff file:
bd ready → the remaining queue; bd list --status=in_progress → empty
```

## This repo (dogfood)

This changeset itself: epic `agentic-5ge`, ten children claimed via
`bd update --claim` + `.beads/session-claims`, closed with reasons as
commits landed (`7e5d7c4`, `9def8d6`, `ab252e4`, `2376d48`). The wired
hook blocked live while claims were open, naming all six then-open ids
(`agentic-wc0 agentic-ehb agentic-58t agentic-za0 agentic-rp6
agentic-57r`, exit 2), and the closed ones cleared it. Resume state is
`bd ready` / `bd list` — no handoff artifact was written at any point.
