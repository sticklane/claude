---
name: critique
description: Runs an adversarial review of a spec, plan, or diff via the critic agent and relays ranked findings. Use before implementing a spec or plan, before committing a nontrivial change, or when the user asks "review this", "poke holes", or "is this ready?". Not the tool for working-diff bug hunts (/code-review), GitHub pull requests (/review), or exercising runtime behavior (the verifier agent).
argument-hint: "[path/to/artifact | 'diff']"
---

Get an adversarial second opinion on $ARGUMENTS. If no argument: an
uncommitted diff exists → review that; otherwise the most recently touched
SPEC.md or plan.

1. Spawn the `critic` agent with a POINTER to the artifact (file path, or
   "the output of `git diff HEAD`"), never the pasted content — the critic
   reads it in its own context. Include one line on what "wrong" looks like
   here (e.g., "this spec feeds /breakdown; ambiguity is the enemy").
2. Relay the verdict and findings verbatim in ranked order. Don't soften
   NOT READY.
3. A reviewer told to find gaps will always find some: recommend fixing
   findings that change behavior or block verification; flag style-level
   findings as optional. Apply fixes only if the user asks or the pipeline
   step you're in requires READY.
4. After fixes, re-run the critic on the changed artifact — a critique you
   didn't re-check is a claim, not a verification.
