# Decision record: ultra-mode orchestration in the existing skills

Date: 2026-07-04
Spec: [`specs/ultra-mode/SPEC.md`](../../specs/ultra-mode/SPEC.md)
Research: [`docs/orchestration-research-2026-07.md`](../orchestration-research-2026-07.md)

## Context

The toolkit's orchestration was split between a deterministic file-based state
machine (drain's committed `Status:` flips) and per-turn model judgment (build,
critique, idea deciding each fan-out live). Claude Code's Workflow tool
("ultracode") now offers scripted orchestration — deterministic fan-out,
barriers, token budgets, adversarial-verify patterns, resumable runs — but the
skills never referenced it, so every ultra-style run was improvised per session.
A verified vendor survey (`docs/orchestration-research-2026-07.md`; deep-research
2026-07-03, every adopted claim 3-vote verified) grounds the design.

## Decision

Add a gated **ultra path** to critique, drain, parallel, build, and idea — no
new skill names. Each ultra path is gated on two conditions, both required: the
ultracode opt-in is active AND the active runtime profile documents an
orchestration section (`runtimes/claude-code.md`). With the gate closed (plugin
installs, eval fixtures — no `runtimes/`) the skills behave byte-for-byte as
today. File artifacts (SPEC.md, task files, `Status:` flips) stay the interface
on both paths, so an interrupted ultra run resumes from disk.

### The adopt / leave-model-driven split

Grounded in the vendors' shared axis: put control flow in deterministic code
where the task is well-defined; reserve model judgment for genuinely open
decisions (research doc, "deterministic-vs-model-driven axis"; Anthropic
building-effective-agents; OpenAI "orchestrating via code makes tasks more
deterministic and predictable").

- **Adopt as scripted control flow** — pipeline chaining across dependency
  groups, capped parallel fan-out in drain (group throughput mode), a bounded evaluator loop
  that prefers runnable acceptance commands over judges, and file-based
  resume-from-checkpoint state.
- **Leave model-driven** — decomposition judgment inside breakdown, routing /
  next-task selection inside `/build`'s bounded mode, and subagent delegation (light-summary
  returns). This is Anthropic's endorsed hybrid: the script owns the loop, the
  model owns the decisions on intermediate results.

### Effort tiers

Dispatch prompts carry Anthropic's proven anti-runaway effort-scaling language
(research doc, "prompted effort-scaling rules rather than hard-coded caps"):
simple fact-finding = 1 agent / 3–10 tool calls; direct comparisons = 2–4
agents / 10–15 calls each; 10+ agents only for genuinely breadth-first work.
Prompted scaling, not hard caps, is what fixed the "50 subagents for a trivial
query" failure mode in Anthropic's production Research system.

### Cost figures (with baseline ambiguity)

Multi-agent orchestration is the expensive path, so it is opt-in only. The
reported multiple is **~10–15×** a single agent — but the baseline is
genuinely ambiguous: Anthropic's June-2025 engineering blog says multi-agent
uses ~15× the tokens of _chat_ (single agents ~4×), while the Dec-2025
whitepaper says ~10–15× the tokens of _a single agent_. The two figures use
different baselines and are self-reported internal numbers; the 90.2%
single-vs-multi eval gain is likewise self-reported. We record the range, not a
point estimate, and treat "is it 4× or 10–15×?" as an open budgeting question
(research doc, Open questions).

### Single-agent default

One agent is the default everywhere; ultra never auto-triggers. The ~10–15×
multiple is spent only on breadth-first or verification-critical work the user
explicitly opts into (OpenAI: "Start with one agent whenever you can. Add
specialists only when they materially improve capability isolation...").

## Deliberate non-adoptions

Two patterns were considered and deliberately NOT adopted:

1. **No auto-ultra heuristics.** Ultra is opt-in only — never triggered by
   task-size or complexity heuristics. The vendors gate multi-agent spend
   behind explicit prompted effort-scaling and a single-agent default, not
   automatic escalation (research doc, "prompted effort-scaling rules rather
   than hard-coded caps"; OpenAI's start-with-one-agent guidance). Auto-
   escalation would spend the ~10–15× multiple without a human deciding the
   breadth-first work is worth it.

2. **No multi-judge voting as the default verifier — single-call rubric judge
   instead.** Verification prefers runnable acceptance commands; where a
   criterion has no runnable check, the fallback is a single LLM call emitting a
   0–1 score plus pass/fail against a rubric, not a multi-judge vote. Anthropic
   found "a single LLM call with a single prompt outputting scores from 0.0–1.0
   and a pass-fail grade was the most consistent and aligned with human
   judgements" (research doc, "Anthropic's verification guidance is layered").
   Voting with several different prompts is reserved for one place — adversarial
   critique — because Anthropic recommends it specifically for reviewing code
   vulnerabilities, not for build-task grading (same finding). The empirically
   best judge configuration for build tasks specifically remains an open
   question (research doc, Open questions).

## 2026-07-04 — /parallel folded into /drain (group throughput mode)

The parallelization and orchestrator-workers building blocks are two
patterns, not two commands. Drain's step 2 already dispatched independent
groups concurrently using its own worker prompt and its own collection —
explicitly not /parallel's — so /parallel had decayed into a citation
shell: its push guard, baton, and worker discipline all pointed back at
drain. Merged as drain's **group throughput mode**; the one behavior
/parallel had that drain lacked — stop on a cross-task merge conflict and
report, instead of slot-machining a conflict a fresh attempt cannot fix —
moved into drain's group-mode merge rules. The human gate is unchanged:
drain stays `disable-model-invocation`, so fan-out spend still requires a
human launch (docs/human-gates.md), and ultra remains drain's doubly
opt-in engine rather than a peer concept.

## 2026-07-06 — surveyed the rest of the skills for ultra-path conversion; none qualify

Prompted by "should we use code to manage workflows anywhere we currently
use text," scouted all six skills that looked mechanical enough to be
candidates on a first pass — breakdown, prioritize, list-specs, gate,
fleet, workboard — against `workflow-author/SKILL.md`'s own admission
criteria: deterministic control flow _over subagents_ (loops, fan-out,
staged verification), explicitly rejecting a "single linear sequence."
None qualify:

- **prioritize** can't compile at all — its core step is an interactive
  human interview, and a Workflow script can't run `AskUserQuestion`
  mid-run.
- **list-specs**, **fleet**, **workboard** are each a single deterministic
  script invocation or a passive TaskList/`git worktree` read with zero
  fan-out — a workflow wrapper adds subprocess/script overhead for no
  orchestration leverage.
- **gate** is one judgment call plus one idempotent installer run, no
  loop.
- **breakdown** comes closest but its only "fan-out" is a few scout calls
  plus one _optional_, single conditional critic call — not the loop/
  fan-out shape a Workflow script exists for.

Being "mechanical" (no model judgment) is necessary but not sufficient —
the real bar is orchestration complexity a script would meaningfully
improve, which none of these six have today. The two skills with genuine
multi-agent fan-out and loops (drain, build) already have ultra paths;
this survey found no gap to close. Revisit if any of these six later
grows real fan-out (e.g. breakdown's critic pass becoming a multi-lens
panel) rather than converting speculatively now.

## Links

- Spec: [`specs/ultra-mode/SPEC.md`](../../specs/ultra-mode/SPEC.md)
- Research: [`docs/orchestration-research-2026-07.md`](../orchestration-research-2026-07.md)
- Closed-gate e2e evidence: [`specs/ultra-mode/evidence/03-closed-gate-e2e.md`](../../specs/ultra-mode/evidence/03-closed-gate-e2e.md)
