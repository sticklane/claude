# Tech debt / follow-ups

- **workboard: surface per-session token/cost.** Anthropic's multi-agent
  research guidance (docs/agent-dashboards.md) says cost belongs on any
  agent-management surface — token usage explains ~80% of performance
  variance. Session records may carry usage data; if so, add a cost column
  to the sessions tables and a total tile. (2026-07-03)
- **workboard: `--abandon` for stale toolkit specs.** The abandon-marker
  mechanism only covers Antigravity conversations; stale `specs/<slug>`
  dirs still require manual `Status: deferred` edits or deletion. Consider
  a symmetric one-command defer. (2026-07-03)
