# Runtime profiles

Core skills, agents, and rules speak four abstract tiers; each profile
in this directory maps those tiers — plus the runtime's headless
command template and orchestration surface — onto one concrete runtime:

- [claude-code.md](claude-code.md) — the default; reproduces today's
  behavior exactly.
- [antigravity.md](antigravity.md) — describes the `antigravity/`
  reference port.
- [gemini-cli.md](gemini-cli.md) — mapping for Google's gemini-cli.

This file is the single home of the selection convention and the
tier-override format. Other files (the drain and autopilot references,
`.claude/agents/scout.md`) cite it; they do not restate it.

## Selecting a runtime

A consuming repo selects its runtime by creating `.claude/runtime.md`
whose first non-comment line is:

```
runtime: <profile-name>
```

where `<profile-name>` names a file here (`claude-code`, `antigravity`,
`gemini-cli`). If the file is absent, the runtime is `claude-code` —
so a repo that never creates `.claude/runtime.md` gets today's behavior
unchanged.

## The four tiers

1. **scout-tier** — cheap, fast, read-only reconnaissance (mechanical
   or lookup work). Claude default: Haiku at low effort.
2. **session-tier** — the conversation's own model; ordinary judgment
   work. Claude default: inherit.
3. **deep-tier** — heavy judgment above the session default: final
   review of a large diff, subtle-bug hunts, architecture critique.
   Claude default: Opus 4.8 (`claude-opus-4-8`).
4. **frontier-tier** — only work that truly needs the strongest model:
   novel architecture decisions, security-critical review, or a retry
   after a deep-tier attempt failed. Claude default: Fable
   (`claude-fable-5`).

## Tier overrides

Lines after `runtime:` may override individual tier mappings, one per
line:

```
<tier-name>: <model>
```

An unlisted scout or session tier keeps the active profile's default.
The two deep tiers are **opt-in**: their rows in a profile's `## Tiers`
table are recommended pin values (what "deep work" means on that
runtime), not active defaults. Dispatchers route deep-tier or
frontier-tier work to a distinct model only when an explicit pin names
that tier — so a file containing only `runtime: claude-code` changes
nothing.

Worked example — exactly how a repo turns the Claude deep-work
defaults ON:

```
runtime: claude-code
deep-tier: claude-opus-4-8
frontier-tier: claude-fable-5
```

Overrides also accept any other model id — e.g. `frontier-tier:
claude-opus-4-8` to cap spend, or a self-hosted model id.

## What tier pins bind

Tier pins bind **dispatchers** — skills that spawn agents via the
harness (drain's tournament workers and per-candidate verifier runs,
/design's candidate investigators, an on-demand verifier escalation):
they consult these pins and pass the mapped model through the harness's
model parameter when spawning. Pins do NOT change the interactive
session's own model, and do NOT reach the headless fallback path in v1
(the frozen `## Headless` templates run their profile's default).
