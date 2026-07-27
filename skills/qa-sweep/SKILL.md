---
name: qa-sweep
description: Tests a deployed app or repo end to end - scouts its surface, checks deploy/migration freshness FIRST, dispatches parallel per-domain test agents, files specs for confirmed breakage, self-chains into /critique, then hands off to /drain (or chains into it when the request authorized fixing) and re-verifies. Trigger phrases - "test the site", "QA sweep", "run a smoke test", "test everything end to end", "shake out what's broken".
---

Read and follow [the canonical workflow](../../.claude/skills/qa-sweep/SKILL.md) completely before acting. Resolve every relative link in that file against its own directory. This packaging entrypoint contains no workflow procedure; the linked file remains the single source of truth.
