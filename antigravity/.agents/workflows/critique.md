---
description: Adversarially review a spec, plan, or diff; high-signal findings only
---

Use the critic skill (.agents/skills/critic/SKILL.md) and follow it exactly, applying it to whatever arguments follow the command. If no arguments were given and the skill needs a target, ask for it. If the target touches auth, payments, secrets, or user-data handling, tell the critic to review with an explicit security lens (Antigravity has no built-in /security-review; the lens instruction is the whole mechanism here).

Relay the verdict and findings verbatim in ranked order. Don't soften NOT READY.

If the target is a `SPEC.md`: on a READY verdict, write `Breakdown-ready: true` as a header line under the spec's title (above the first `##`) — this is the token drain reads to auto-invoke the breakdown workflow on specs with no `tasks/` yet. On NOT READY, remove a stale `Breakdown-ready:` line if one is present — a spec that regressed shouldn't keep an old authorization. Never write or remove this marker for a plan or diff target.

A reviewer told to find gaps will always find some: recommend fixing findings that change behavior or block verification; flag style-level findings as optional. Apply fixes only if the user asks or the pipeline step you're in requires READY. After fixes, re-run the critic on the changed artifact — a critique you didn't re-check is a claim, not a verification. Between rounds the author re-reads only the sections the critic named, never the whole artifact.

## Ultra path

Antigravity has no Workflow tool and no runtime profile, so the ultra
critic-panel path is permanently closed here — the single critic above is
always the path. (For reference: in the Claude Code toolkit, an opted-in
ultracode run against an orchestration-documenting profile fans a 3–5
lens-diverse panel with dedupe + majority-refute verify. That gate never
opens in this mirror.)
