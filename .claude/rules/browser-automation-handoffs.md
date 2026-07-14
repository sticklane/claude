# Browser-automation handoffs

A claude-in-chrome-driven flow that hits a login wall it cannot clear should
detect it and hand off fast, not grind through alternate strategies. In a
real session, four distinct click strategies were tried against a Google
SSO/One-Tap login chip before the run finally handed off to a human — wasted
effort a fast detect-and-handoff rule would have avoided (task evidence,
`specs/qa-sweep-skill-promotion`). Google SSO/One-Tap is a recurring dead end
for browser-driven testing: the chip is rendered in a cross-origin iframe the
automation can neither see into nor reliably dismiss, so extra attempts
almost never succeed and each one burns a round-trip.

## The rule

Any claude-in-chrome-driven flow that detects a Google SSO/One-Tap
(single sign-on) login surface attempts **at most ONE** click strategy
against it, then hands off to the human — it does not retry alternate click
strategies against the same surface. One attempt is the whole budget; on its
failure the flow stops and surfaces the handoff rather than escalating to a
second, third, or fourth strategy.

## Scope

- This governs the SSO/One-Tap login-wall case specifically — a surface the
  automation structurally cannot clear on its own. It is not a blanket
  one-retry cap on every click a browser flow makes.
- Skills that drive claude-in-chrome cite this rule for the handoff behavior
  rather than restating it inline (this repo's "cite it, don't restate it"
  convention for shared doctrine).
