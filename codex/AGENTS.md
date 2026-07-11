# Agentic development toolkit — Codex CLI port

This directory is the Codex CLI port of the toolkit. The shared pipeline
orientation — precedence, token/context discipline, the idea → spec →
(design) → breakdown → build/drain → distill flow, and how every stage
hands off through a file on disk — lives in
[`antigravity/AGENTS.md`](../antigravity/AGENTS.md); read it first. The
skills under `.agents/skills/` here are relative symlinks into the
antigravity skill tree, so they stay in lockstep with it.

## Codex-specific fact

Unlike the antigravity port, this project additionally exposes
`drain`, `build`, `autopilot`, and `evals` as explicit-invocation-only
skills — never auto-triggered. Invoke them with `$drain`, `$build`,
`$autopilot`, `$evals`, or through the `/skills` command.

See [`codex/README.md`](README.md) for the experimental-reliability caveat
on this port.
