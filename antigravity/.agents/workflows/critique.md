---
description: Adversarially review a spec, plan, or diff; high-signal findings only
---

Use the critic skill (.agents/skills/critic/SKILL.md) and follow it exactly, applying it to whatever arguments follow the command. If no arguments were given and the skill needs a target, ask for it. If the target touches auth, payments, secrets, or user-data handling, tell the critic to review with an explicit security lens (Antigravity has no built-in /security-review; the lens instruction is the whole mechanism here).

**SPEC.md re-run skip (check this before dispatching the critic).** When the target is a `SPEC.md`, hash its current bytes (e.g. `sha256sum specs/<slug>/SPEC.md`) and compare against the hash recorded in the header of `specs/<slug>/critique-findings.md`, if that file exists and carries a parseable hash. If the hash matches AND a verdict is already recorded there, skip the critic dispatch entirely and relay that recorded verdict and its findings — the answer was already computed against byte-identical content. A missing findings file, a missing header hash, or a hash that won't parse always means "run the critic" (never treat an absent or unparseable hash as a match — findings files written before this skip shipped carry no hash, so they always re-run). The skip is `SPEC.md`-only: a plan or diff target has no findings file to compare against and always dispatches.

Relay the verdict and findings verbatim in ranked order. Don't soften NOT READY.

If the target is a `SPEC.md`: on a READY verdict, write `Breakdown-ready: true` as a header line under the spec's title (above the first `##`) — this is the token drain reads to auto-invoke the breakdown workflow on specs with no `tasks/` yet. On NOT READY, remove a stale `Breakdown-ready:` line if one is present — a spec that regressed shouldn't keep an old authorization. Never write or remove this marker for a plan or diff target.

**Triage the findings** when the verdict is NOT READY or READY WITH NITS. Classify each finding as MECHANICAL — an edit with no judgment call: a stale path/line reference, a non-deterministic or under-scoped acceptance command, a missing runnable check, a format/header contract violation — or JUDGMENT — an ambiguity, a scope question, a missing design decision, a contested tradeoff. MECHANICAL findings are applied unconditionally, without the user-ask/pipeline gate that governs the rest: edit the target directly, commit, and re-run the critic. This apply→recheck loop is bounded to the 2–4-cycle evaluator-optimizer cap the token-discipline rule sets. Auto-apply is scoped to a prose target only — a `SPEC.md`, or the plan file when the critique reviewed a plan; a working-diff or code target is never auto-edited. For the JUDGMENT findings (and any MECHANICAL finding still open after the loop bound): a reviewer told to find gaps will always find some — recommend fixing the ones that change behavior or block verification, flag style-level ones as optional, and apply these only if the user asks or the pipeline step you're in requires READY. Nothing is dropped silently — every still-open finding is relayed.

After fixes, re-run the critic on the changed artifact — a critique you didn't re-check is a claim, not a verification. Between rounds the author re-reads only the sections the critic named, never the whole artifact.

**Persist the findings for a `SPEC.md` target** (skip for a plan or diff, and skip when the re-run skip above already relayed a recorded verdict — nothing was re-derived). Once the verdict has settled, if it is NOT READY or READY WITH NITS, write or update `specs/<slug>/critique-findings.md` in one atomic write: a header recording the content hash of the exact `SPEC.md` bytes the settled verdict was produced from together with that verdict, and the findings as a dated section. Header hash and findings are written together so the recorded hash can't desync from the findings it describes; that hash is what the next invocation's re-run skip compares against. A plain READY with no nits records no findings — the `Breakdown-ready:` marker is its only artifact.

## Ultra path

Antigravity has no Workflow tool and no runtime profile, so the ultra
critic-panel path is permanently closed here — the single critic above is
always the path. (For reference: in the Claude Code toolkit, an opted-in
ultracode run against an orchestration-documenting profile fans a 3–5
lens-diverse panel with dedupe + majority-refute verify. That gate never
opens in this mirror.)
