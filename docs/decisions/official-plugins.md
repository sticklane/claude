# Decision record: leaning on the official knowledge-work plugins

Date: 2026-07-06
Spec: none — direct investigation (branch `claude/official-plugins-evaluation-26if0d`)
Research: agent inventory of `anthropics/knowledge-work-plugins` and
`anthropics/claude-plugins-official`, 2026-07-06 — condensed below; no
separate research doc.

## Context

Anthropic ships official role plugins for engineering, design, product
management, and data. They live in the `knowledge-work-plugins` marketplace
(https://github.com/anthropics/knowledge-work-plugins, Apache-2.0, ~80
marketplace entries), which is **separate** from `claude-plugins-official`
(the 255-entry Claude Code directory the playbook already cites as S19–S21).
Zero cross-references exist between the two manifests. Naming gotcha: the
`data` plugin in claude-plugins-official is Astronomer's Airflow plugin, not
the data role plugin.

All four role plugins are already enabled in this workspace's claude.ai
catalog, so Cowork and claude.ai sessions can invoke them today at no
adoption cost.

### What they ship

Skills plus optional MCP connector manifests (`.mcp.json` + CONNECTORS.md)
— **no agents, no hooks, no orchestration**. Prompt-only domain knowledge.

| Plugin             | Version | Skills (condensed)                                                                                                                                                                                                                |
| ------------------ | ------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| engineering        | 1.2.0   | architecture (ADRs), code-review, debug, deploy-checklist, documentation, incident-response, standup, system-design, tech-debt, testing-strategy                                                                                  |
| design             | 1.2.0   | accessibility-review, design-critique, design-handoff, design-system, research-synthesis, user-research, ux-copy                                                                                                                  |
| product-management | 1.2.0   | competitive-brief, metrics-review, product-brainstorming, roadmap-update, sprint-planning, stakeholder-update, synthesize-research, write-spec                                                                                    |
| data               | 1.1.0   | analyze, explore-data, write-query, create-viz, build-dashboard, validate-data; 3 reference skills (`user-invocable: false`); data-context-extractor (generates a company-specific analysis skill; only one with bundled scripts) |

Connectors are optional per-category HTTP MCP servers (GitHub, Linear,
Slack, Figma, Datadog, BigQuery, Amplitude, …); several entries are
empty-URL placeholders. READMEs drift from directory contents in three of
the four plugins (miscounted or renamed skills) — fine as content, below
this repo's authoring bar.

This toolkit is the opposite shape: orchestration, gates, and discipline
rules with little standalone domain content. The existing precedent is
docs/anthropic-playbook.md mining official plugin prompts as _sources_
(S19 code-review, S20 marketplace variant, S21 code-simplifier) while the
toolkit implements natively.

## Decision

Lean on the role plugins as **user-level complements, never pipeline
dependencies**, and keep the mine-as-sources pattern for doctrine.

1. **No pipeline stage, skill, or task acceptance criterion may depend on
   them.** Unattended workers don't carry user-level plugins — the same
   reasoning that bars gating acceptance on the Workflow tool
   (docs/memory/unattended-worker-tool-limits.md). Their skills also carry
   none of the gate/verification discipline the pipeline assumes, and
   several of their connectors need interactive auth that headless runs
   lack.
2. **Do not vendor or fork them into `.claude/skills/`.** Vendoring ~35
   skills would double the antigravity/ mirror burden and take over
   maintenance Anthropic already does (versioned, actively updated).
   Marketplace enablement keeps them current for free.
3. Per-plugin verdicts:
   - **engineering — mostly subsumed; don't lean on it.** The harness
     built-ins (/code-review, /security-review, /simplify) are the
     stronger, false-positive-filtered descendants of its review content,
     and quality-discipline.md covers TDD/testing strategy. Residual
     value: incident-response and ADR content as playbook _sources_ if the
     toolkit ever grows those topics.
   - **product-management — complement upstream of /idea.**
     synthesize-research, competitive-brief, and metrics-review produce
     the raw material an /idea interview consumes. Its write-spec is a
     human-facing PRD skill, distinct from /idea's agent-ready SPEC.md
     with runnable acceptance criteria — different artifacts, real
     trigger-phrase collision (see 4).
   - **design — pure complement; lean on it freely.** accessibility-review,
     design-handoff, and ux-copy have no toolkit counterpart and slot
     directly into front-end work.
   - **data — complement for analysis work.** Chart/dashboard styling in
     create-viz can conflict with an environment's dataviz skill; the
     precedence order (live request → executing skill) resolves it.
     data-context-extractor — a skill that interviews experts and emits a
     company-specific skill — is a pattern worth studying for /distill and
     /onboard.
4. **Trigger-collision guard.** With role plugins enabled beside the
   toolkit, description testing (CLAUDE.md "Testing changes") gains
   external neighbors: "write a spec" (/idea vs write-spec), "how should
   we architect this" (/design vs architecture/system-design), roadmap and
   priority phrasing (/prioritize vs roadmap-update/sprint-planning). When
   editing those toolkit descriptions, verify routing in a session with
   the role plugins enabled.
5. **In-repo change: this record only.** Playbook source rows get added
   when a skill actually draws on plugin content, not preemptively.
