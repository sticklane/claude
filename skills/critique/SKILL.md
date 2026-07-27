---
name: critique
description: Runs an adversarial review of a spec, plan, or diff via the critic agent and relays ranked findings. Use before implementing a spec or plan, before committing a nontrivial change, or when the user says "critic", "critique", "run the critic", "run a critique", "review this spec", "review this plan", "poke holes", or "is this ready?" — "critic" and "critique" both name this skill, whichever word the user reaches for. Route a bare review-this request by its artifact — a spec, plan, or diff here; a README, AGENTS.md, or docs/ page to /prose-review. Not the tool for prose quality in a human-facing doc (/prose-review), working-diff bug hunts (/code-review), GitHub pull requests (/review), or exercising runtime behavior (the verifier agent).
---

Read and follow [the canonical workflow](../../.claude/skills/critique/SKILL.md) completely before acting. Resolve every relative link in that file against its own directory. This packaging entrypoint contains no workflow procedure; the linked file remains the single source of truth.
