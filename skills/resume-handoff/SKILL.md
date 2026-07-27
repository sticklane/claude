---
name: resume-handoff
description: Deterministically resumes work parked in bd by /handoff or a session-refresh — finds the open `handoff`-labeled issue, reads it and the issues it tracks, resumes the recorded next step, then closes the handoff issue so the handoff-resume hook goes quiet again. Use when the user says "resume", "resume handoff", "continue from the handoff", "pick up where we left off", or invokes "/resume-handoff"; also the deterministic target the handoff-resume SessionStart hook's advisory now names, replacing ad hoc read-and-continue prose.
---

Read and follow [the canonical workflow](../../.claude/skills/resume-handoff/SKILL.md) completely before acting. Resolve every relative link in that file against its own directory. This packaging entrypoint contains no workflow procedure; the linked file remains the single source of truth.
