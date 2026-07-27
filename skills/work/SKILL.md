---
name: work
description: Runs a session off the bd (beads) issue queue - answers "what should I do", tracks it in the tracker, and fans work across agents when it is parallel. Session start pulls the ready queue; the picked issue is claimed before work and closed on done; discovered work is filed back with a discovered-from link; unfamiliar code is scouted, never bulk-read. Trigger phrases - "/work", "what's next", "work the queue", "track this", and fan-out asks "fan out", "parallelize this", "spread across agents".
---

Read and follow [the canonical workflow](../../.claude/skills/work/SKILL.md) completely before acting. Resolve every relative link in that file against its own directory. This packaging entrypoint contains no workflow procedure; the linked file remains the single source of truth.
