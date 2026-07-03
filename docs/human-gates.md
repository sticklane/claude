# Why humans launch the gated stages

Five skills carry `disable-model-invocation: true` — /build, /parallel,
/autopilot, /drain, /evals — so only a human can start them. Everything
else in the pipeline is model-invocable, and light artifact stages may
self-chain (CLAUDE.md conventions). This file is the canonical rationale
for where the human gates sit; skills and CLAUDE.md cite it rather than
restating it.

## The five reasons

1. **Spend discontinuities are the user's to authorize.** Ungated stages
   produce text; gated stages multiply agents: one /build is a worker +
   scouts + verifier, /parallel is N of those, /drain is a whole queue,
   a tournament triples a task, /evals launches paid headless sessions.
   Vendor cost anchors: agents ≈4× chat tokens, multi-agent ≈15×
   (external-playbooks.md). A model that can self-trigger the 15× step
   will sometimes do it eagerly and wrongly — the effort-complexity
   mismatch antipattern. The human trigger is the budget signature.
2. **Autonomy is classified, not assumed — and the classifier must not
   be the beneficiary.** /autopilot and /drain open with the
   peripheral/core classification gate (anthropic-playbook.md, "How they
   let agents run unattended"). A model invoking them would classify its
   own request for autonomy and then grant it — the same conflict the
   independent verifier exists to prevent for code.
3. **Blast radius jumps at the execution boundary.** Pre-gate failures
   are bad files you delete; post-gate failures are commits, merges,
   branch surgery, and status flips compounding at machine speed. The
   walk-away contract ("recovery is discard-the-branch") only holds if a
   human chose the launch point, isolation, and success gate first. The
   gate sits at the last point where a wrong spec costs ~1% of what it
   costs after.
4. **A hard mechanism beats a soft rule where injection could
   escalate.** Unattended workers read unvetted repo content. The
   untrusted-data rule says injected instructions carry no authority —
   but a rule is prose. `disable-model-invocation` removes gated skills
   from the model's context entirely (and blocks scheduled firing), so
   injected text can never transitively become a fleet of launched
   workers. "Shouldn't" becomes "can't" exactly where escalation would
   be catastrophic.
5. **The vendors converge on this boundary.** OpenAI mandates human
   intervention at retry thresholds and high-risk actions; Claude Code's
   own auto-mode classifier denies "launching an autonomous agent loop
   without human approval or a sandbox"; the playbook's walk-away
   contract is signed by a human. The gated five are precisely the
   autonomous-loop launchers (external-playbooks.md, "Adopted from
   OpenAI" and "Skill chaining").

## What the gate is not

It is not per-step supervision: one trigger buys an entire autonomous
run — /drain dispatches, verifies, merges, and bookkeeps a whole queue
after a single "go". The triggers mark boundaries between cheap
reversible planning and expensive compounding execution, nowhere else.

## Calibrated, not dogmatic

The boundary moves deliberately: light artifact stages self-chain
because their outputs are cheap, reversible, and already gated by the
critic's READY verdict. As models improve, the playbook's own advice is
to delete scaffolding — these gates are the part designed to be deleted
last, and only ever by a human editing the frontmatter.
