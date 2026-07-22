# Architecture pivot: skill-augmented native orchestration

Decision date: 2026-07-22. Ratified by the maintainer in a live
session. Normative dispositions live in
`specs/agentic-core-redesign/SPEC.md` (addendum) and in task headers.
This document explains the decision. It does not add requirements.

## The decision

Claude Code is the primary runtime. Native ultracode workflows are the
execution engine for multi-agent work. Portability is data-level: any
agent can read the bd queue, the ctx index, and the task files. No
runtime is guaranteed to run the same procedures. Cost control is
advisory plus a thin guard: native runtime caps, cheap-model routing
in every authored script, agentprof attribution after the fact, and a
pre-flight estimate before large fan-outs. There is no metered ledger.

## Why

The evidence came from three sources: an audit of this repo, live
instrumented ultracode runs, and external research on how
practitioners run beads and native workflows.

1. Procedure-level portability was the most expensive requirement in
   the repo. It produced the two mirror trees, the parity gates, two
   rules files, the adapter plans, and a nine-task plan to replicate
   ultracode. None of that work made anything run better on the
   runtime actually in use.
2. The native engine already does what the replication would have
   built. Per-stage model routing is documented and was verified
   live. Context isolation is structural: intermediate results stay
   in script variables, and every subagent starts blank. Schema'd
   returns, resume, concurrency caps, and the live progress view all
   ship with the platform.
3. Advisory prose does not control agent behavior; mechanisms do.
   Measured compliance with "prefer X" prose was zero. The community
   reports the same failure with beads. The fix is a hook and a
   default, not more prose.
4. A full enforcement ledger protects against risks a solo operator
   does not carry. Approvals blocked twenty-four ready tasks while
   the measured cost leaks happened anyway. Caps and visibility are
   the proportionate control.

## What goes away

| Item                                                                                                                              | Disposition                                                                           | Why                                                                                                                               |
| --------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------- |
| `antigravity/` and `codex/` mirror trees                                                                                          | Deleted (core task 10, unblocked); each becomes one README pointing at the data layer | Procedure parity is no longer a requirement; the trees were hand-maintained triplication                                          |
| Mirror machinery: both mirror rules files, the procedure manifest, the coverage test, three parity tests                          | Deleted with the trees                                                                | They guarded the thing being deleted, and the coverage gate could not catch the failure modes it existed for                      |
| The composer (`agentic compose`, meter, envelope)                                                                                 | Obsolete                                                                              | Native workflows provide schema'd returns, tier routing, and context isolation; the two fragments worth keeping are small scripts |
| The custom work loop (`agentic loop`)                                                                                             | Obsolete                                                                              | The drain becomes a skill-authored saved workflow over `bd ready`                                                                 |
| The `agentic ctx` wrapper                                                                                                         | Obsolete                                                                              | ctx works standalone; the wrapper added a layer without adding capability                                                         |
| The dynamic-workflows build (dispatch, run, watch — nine tasks)                                                                   | Parked behind the head-to-head verdict                                                | It replicated the native engine; its unique additions answer needs that are not currently binding                                 |
| Launch-authorization contracts in build, drain, and prioritize                                                                    | Deleted (core task 11)                                                                | Caps protect spend; approvals only blocked work                                                                                   |
| Drain's prose machinery: batons, owner leases, generation counters, flip-commit recovery                                          | Deleted (core task 09)                                                                | A prose orchestrator loses its place; bd state is the resume                                                                      |
| Handoff artifacts for drains; the fleet view's overlap with native `/workflows`; list-specs and prioritize as standalone scanners | Retire or thin at cutover                                                             | bd answers "what next" and "where was I"; the platform renders running agents                                                     |
| Most rules-file volume                                                                                                            | Classified and shrunk (core task 13)                                                  | A rule that can be mechanized becomes code; one that cannot is either context doctrine or a dead letter                           |

## What stays

| Item                                                                                                             | Role                                                         | Why it stays                                                                                                        |
| ---------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------- |
| beads (`bd`, pinned) plus the glue: curated init, shadow sync, committed JSONL                                   | The state layer: tasks, dependencies, claims, provenance     | Nothing native provides cross-session project state; the data layer is also what makes the work portable            |
| ctx                                                                                                              | Code-structure index: symbol maps, references, durable notes | Differentiated; no native equivalent; adoption comes from injection, which the skills own                           |
| The judgment skills: idea, critique, breakdown, build, distill, prose-review, qa-sweep, factcheck, deep-research | Taste and adversarial checking                               | They are the augmentation in "skill-augmented"; prompts encode judgment that neither the tracker nor the engine has |
| The critic and verifier agents                                                                                   | Independent adversarial review                               | Same reason; every artifact this pivot produced went through them                                                   |
| The gate skill and its Stop hook                                                                                 | Deterministic quality enforcement                            | Hooks are the one mechanical enforcement point the harness offers; everything mechanical routes through them        |
| The untrusted-data rule and the injection screen                                                                 | Security boundary                                            | Unchanged by any architecture; tracker text entering prompts is still screened                                      |
| agentprof                                                                                                        | Cost attribution                                             | The watch half of advisory cost control; it produced the numbers behind this decision                               |
| The evals machinery                                                                                              | Behavioral regression tests for skills                       | The only way to know a prose skill still works after an edit                                                        |
| The head-to-head eval harness                                                                                    | The empirical check on this decision                         | Arm S′ is exactly the new architecture; if the data disagrees with this document, the data wins                     |
| Acceptance-command discipline and Touch-disjoint scheduling                                                      | Task quality and safe parallelism                            | Consumed unchanged by the bd-backed drain flow                                                                      |

## What is new

Three small things replace the machinery.

1. **The beads-daily skill** (`specs/beads-daily-skill`). The attended
   default. Prime from bd at session start. Claim before working.
   Close on done. File discovered work with provenance. When work
   fans out, author a native workflow with cheap tiers on mechanical
   stages, and file kept results to bd before the run ends.
2. **The bd-compliance Stop hook.** A session cannot end "done" while
   bd issues it claimed sit open. This converts the known compliance
   failure — agents forgetting the tracker mid-session — into a
   refusal.
3. **The pre-flight fan-out guard.** A script estimates agent count
   times the measured per-agent floor against a threshold and
   requires an explicit override above it.

## What changes in daily work

Session start is `bd prime` and "what's next" is `bd ready`. Small
work happens directly. Parallel work happens through a native
workflow the skill authors, with tier routing in the script. Results
that matter end up in bd, enforced by the hook. Resume is a query,
not a handoff file. Other runtimes remain able to read everything and
work tasks with their own abilities; they no longer receive ported
procedures.

## References

- Normative addendum: `specs/agentic-core-redesign/SPEC.md`
- Centerpiece spec: `specs/beads-daily-skill/SPEC.md`
- Parked: `specs/agentic-dynamic-workflows/SPEC.md`
- Measurement: `specs/skills-vs-ultracode-eval/SPEC.md`
- Evidence for the numbers cited: the EVIDENCE.md files of the specs
  above
