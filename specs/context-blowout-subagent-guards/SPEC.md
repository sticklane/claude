Status: open
Priority: P2

## Problem

A cross-session research sweep found two related, unfixed gaps in this
repo's own token-discipline guidance, both of the same shape: a documented
safety step exists somewhere, but isn't reinforced at the place a session
actually needs it, so it gets skipped under pressure.

**Screenshot-heavy browser walks blow context.** A `claude-in-chrome`-driven
site walk took a full screenshot after nearly every navigation. Roughly
2.7MB of a 5.9MB session transcript was tool output, and the session died
mid-task with "Prompt is too long" before it filed any of the specs it was
investigating for. A same-task RETRY on a later session succeeded by
delegating page-by-page scouting to subagents and using direct screenshots
sparingly in the main session. The fix already works in practice; nothing
in this repo mandates it.

`.claude/rules/token-discipline.md`'s "Delegation defaults" section states
the general principle ("never read files into main context to look
around... use scout") and even has a precedent for a tool-specific
addition (the `large-codebase-context-guide` spec's ToolSearch bullet at
lines 42–50), but says nothing about browser automation specifically —
`claude-in-chrome` is a third-party plugin skill (not authored in this
repo; confirmed by a repo-wide search that turned up no
`claude-in-chrome`-specific rule, skill, or doc anywhere under
`/Users/sjaconette/claude`), so nothing in the repo's own guidance
constrains how a session uses it.

**Deferred-tool blind calls waste round trips.** In two separate sessions
(different repos), a `Monitor` tool call was made with a guessed parameter
name without first `ToolSearch`-loading its schema, throwing
`InputValidationError` and wasting a full round trip. The "load the
schema before calling" discipline is already stated — but only inside the
`claude-in-chrome` MCP server's own bundled instructions (its "batch
every tool you expect to need into ONE ToolSearch call" guidance), which
is harness/plugin-supplied and outside this repo's control, and inside
the harness's own per-session system-reminder that lists deferred tools.
Neither reinforcement stopped the guessed-parameter call. This repo's
`token-discipline.md` has a "Dispatch authoring" section that already
states loop bounds, tier choices, and other explicit dispatch-prompt
requirements — but says nothing about deferred-tool schema loading, so a
dispatch prompt for a worker likely to hit `Monitor` or a similar deferred
tool carries no reminder beyond the harness's own (evidently
insufficient) system-reminder.

Both gaps share a root cause: a proven-working practice exists but isn't
promoted from "worked once" to "required," and the user's explicit
directive for closing this class of gap is that the fix mechanism must be
**subagent delegation**, not "be more careful" prose.

## Solution

Extend `.claude/rules/token-discipline.md` in two places, each adding a
bullet in the section's existing style (bold lead-in, then explanation,
then citation) rather than a new section or file:

1. **"Delegation defaults"** (after the existing `ToolSearch`/code-search
   bullet, lines 42–50) gets a new bullet mandating subagent delegation
   for multi-page/multi-step browser-automation walks: each page-check is
   routed through a subagent that returns a short structured verdict, not
   raw screenshots held in the orchestrating session's context; direct
   in-context screenshots are capped at a small anchored number per turn
   (2), with anything beyond the cap required to go through a subagent.
   The bullet cites the RETRY evidence above as the proven pattern to
   follow, and cites this section's own opening bullet (`scout` for
   where/how/what-exists) as the delegation vehicle for pages that are
   pure existence/state checks, reserving `general-purpose` or a
   purpose-built agent for pages needing an interaction sequence
   (`scout` is `Read/Grep/Glob`-only per `.claude/agents/scout.md` and
   cannot drive `mcp__claude-in-chrome__*` tools).

2. **"Dispatch authoring"** (which already has bullets for loop bounds,
   tier choice, and return-size caps) gets a new bullet generalizing the
   "load a deferred tool's schema via `ToolSearch` before calling it"
   discipline beyond `claude-in-chrome`: any dispatch prompt for a worker
   likely to touch a deferred tool (the evidenced case, `Monitor`, named
   explicitly, plus the general class) must include an explicit reminder
   to `ToolSearch`-load its schema first, batched in one call rather than
   probed one tool at a time — mirroring the pattern the `claude-in-chrome`
   MCP server's own instructions already use for its tools, but stated
   here for the case (a dispatched worker calling `Monitor` or another
   deferred tool) that has no equivalent per-tool reminder today. This is
   scoped to what a dispatch prompt can add on top of the harness's own
   system-reminder, not a claim that this repo can change the harness's
   reminder mechanism itself — the evidence shows the harness-level
   reminder alone did not prevent the guessed-parameter call, so an
   explicit in-prompt reminder is the additional layer this repo's own
   guidance can supply.

No skill file, agent definition, or `.claude/skills/` content changes —
both edits land entirely inside `.claude/rules/token-discipline.md`.

## Research grounding

> "A `claude-in-chrome`-driven site walk took a full screenshot after
> nearly every navigation. Roughly 2.7MB of a 5.9MB session transcript
> was tool output... The session died mid-task with 'Prompt is too long'
> before it managed to file any of the specs it was investigating for."

> "A same-task RETRY on a later session succeeded by delegating
> page-by-page scouting to subagents and using direct screenshots
> sparingly in the main session — i.e., the subagent-delegation approach
> is already proven to work here, just not mandated anywhere."

> "In two separate sessions (different repos), a `Monitor` tool call was
> made with a guessed parameter name without first `ToolSearch`-loading
> its schema, throwing `InputValidationError` and wasting a full round
> trip."

> claude-in-chrome MCP server instructions (this session's own system
> prompt): "load them with ToolSearch before calling them, and batch
> every tool you expect to need into ONE ToolSearch call... Do NOT load
> tools one at a time; each separate ToolSearch call wastes a full
> round-trip."

## Requirements

- **R1**: `.claude/rules/token-discipline.md`'s "Delegation defaults"
  section gains a new bullet (inserted after the existing `ToolSearch`
  code-search-MCP bullet, before the `## Model and effort matching`
  header) that: (a) requires multi-page/multi-step browser-automation
  walks to route each page-check through a subagent returning a short
  structured verdict rather than accumulating raw screenshots in the
  orchestrating session; (b) states a concrete cap of 2 direct-context
  screenshots per turn, with delegation required beyond that; (c) cites
  the RETRY-succeeded-via-delegation evidence as the model to follow.
- **R2**: `.claude/rules/token-discipline.md`'s "Dispatch authoring"
  section gains a new bullet requiring dispatch prompts for workers
  likely to call a deferred tool (naming `Monitor` as the evidenced case)
  to explicitly remind the worker to batch-load the tool's schema via
  `ToolSearch` before calling it, rather than relying solely on the
  harness's own system-reminder.
- **R3**: Neither new bullet duplicates prose already stated elsewhere in
  the file — each cites the relevant existing bullet/section (the
  `scout` agent's tool grant for R1, the harness system-reminder
  insufficiency for R2) instead of restating it.
- **R4**: No `.claude/skills/` SKILL.md, `.claude/agents/*.md`, or mirror
  path (`antigravity/`, `codex/`) is touched by this spec's requirements
  — confirmed during research that this repo's rules directory
  (`.claude/rules/`) has no mirrored counterpart under `antigravity/` (no
  `rules/` directory exists there), so the CLAUDE.md mirror-obligation
  note does not apply here; any breakdown task should note this rather
  than add an unnecessary mirror step.

## Out of scope

- Editing the `claude-in-chrome` plugin's own bundled MCP-server
  instructions (external, not owned by this repo).
- Changing the harness's per-session deferred-tool system-reminder
  mechanism (harness-level, outside this repo's control).
- Building tooling to enforce the screenshot cap mechanically (a hook,
  a lint check); this spec is doctrine-only, matching how the existing
  `large-codebase-context-guide` precedent bullet was landed.
- Any change to `.claude/agents/scout.md`'s tool grant.

## Acceptance criteria

- `grep -c "route each page-check through a subagent" .claude/rules/token-discipline.md` → 1 (currently 0; confirms R1's bullet landed with this or an equivalent literal anchor — adjust the exact phrase during breakdown if wording changes, keeping the anchor check in sync).
- `grep -c "ToolSearch-load its schema before calling" .claude/rules/token-discipline.md` → 1 (currently 0; confirms R2's bullet landed).
- `grep -n "^## Delegation defaults" .claude/rules/token-discipline.md` and `grep -n "^## Dispatch authoring" .claude/rules/token-discipline.md` each still return exactly one match (sections not duplicated or renamed).
- `grep -c "^## " .claude/rules/token-discipline.md` returns the same count as before the change (8 sections; new content is bullets inside existing sections, not new headers) — verify against `git show HEAD:.claude/rules/token-discipline.md | grep -c '^## '` at breakdown time.
- MANUAL: a human or reviewing agent reads both new bullets in context and confirms they cite rather than restate the RETRY evidence and the `scout` tool-grant constraint, per R3.

## Open questions

- The 2-screenshots-per-turn cap is this spec's proposed anchored default,
  chosen as a small concrete number per the task brief's own suggestion
  (1–2); a human may want a different number based on how the actual
  `claude-in-chrome` skill/workflow gets built out later.
- If a future spec adds a dedicated `claude-in-chrome`-usage rule file or
  skill section to this repo (none exists today), this spec's R1 bullet
  should be migrated there rather than left permanently in
  `token-discipline.md`'s general "Delegation defaults" section — noting
  this now so it isn't lost.
