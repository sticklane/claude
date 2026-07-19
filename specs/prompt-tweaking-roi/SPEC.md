Status: open
Priority: P3
Breakdown-ready: true

## Problem

This session found and disabled a global Claude Code plugin, `prompt-improver`
(severity1-marketplace, v0.6.1, user scope), that wrapped every single
`UserPromptSubmit` event — including system-generated background-agent
notifications, which are not prompts needing clarity evaluation — in up to
five stacked "nudge" text blocks (a "PROMPT EVALUATION" clarity-check
wrapper, plus separate nudges for approach-assessment, workflow-routing,
output-readability, ask-user-question, and plan-mode). It fired 27,500+
times across this account's history; its `improve` nudge duplicated the
full original prompt/notification text inside its own
`Original user request: "..."` wrapper, roughly doubling token cost on
many turns. That plugin is already disabled — fixing it is not this
spec's job (see Non-goals). What it leaves open is the general question:
does mid-flow, dynamic prompt injection have a real place in an agentic
coding workflow at all, and if so, under what conditions — separate from
that one plugin's failure mode?

**The research says: yes, but only for genuinely dynamic, state-dependent
content — never for static reminders a system prompt already covers.**
Three converging sources:

1. Anthropic's own context-engineering guidance states the discipline
   directly: "you should be striving for the minimal set of information
   that fully outlines your expected behavior" and describes "context
   rot" — "as the number of tokens in the context window increases, the
   model's ability to accurately recall information from that context
   decreases" — as an architectural cost of the transformer's n² pairwise
   attention, not a hypothetical. The same post recommends "just-in-time"
   dynamic loading specifically for content that cannot be known
   statically (runtime file paths, stored queries, live results), while
   favoring pre-computed/static context for speed-critical, stable
   information. (Anthropic, "Effective context engineering for AI
   agents," Sept 2025 —
   https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)
2. The "Lost in the Middle" finding (Liu et al., Stanford/UNC, 2023,
   arXiv:2307.03172) shows LLM recall follows a U-shaped curve across a
   long context — strong at the start and end, degraded in the middle —
   which is the concrete mechanism behind "more injected text can hurt
   more than it helps," independent of whether that text is prepended,
   appended, or interleaved mid-conversation.
   (https://arxiv.org/abs/2307.03172)
3. Prompt-caching economics make static and dynamic content asymmetric in
   cost, not just in attention quality: Claude's platform docs state that
   caching requires byte-identical content across requests, and that
   moving dynamic content (a timestamp, a session ID, a user-specific
   variable) OUT of a cached prefix and into a separate, later block is
   "one change [that] alone typically moves hit rates from under 10% to
   over 70%." Injecting variable text into what would otherwise be a
   stable, cached system-prompt prefix (the prompt-improver plugin's
   pattern — a nudge block on every single `UserPromptSubmit`) pays
   uncached, full-price generation on every turn it touches.
   (Claude Docs, "Prompt caching" —
   https://platform.claude.com/docs/en/build-with-claude/prompt-caching)

Claude Code's own hooks documentation draws the same line implicitly: it
describes `UserPromptSubmit`/`SessionStart`'s intended use as "contextual
enrichment (like injecting project standards or time-sensitive
information)" — pairing "project standards" (arguably better served by a
static file) with "time-sensitive information" (which by definition
cannot live in a static prompt). (Claude Code Docs, "Hooks reference" —
https://code.claude.com/docs/en/hooks) The prompt-improver plugin injected
neither — its nudges were static, generic process reminders
("did you evaluate approach X", "consider asking the user") that don't
change turn to turn, which is exactly the shape official guidance and the
caching mechanics above say does NOT belong in a per-turn injection.

**This repo's own hooks already get this right, by convention rather than
by any written rule.** A scout pass over `.claude/hooks/*.sh` and
`hooks/*/` found three `SessionStart`/`UserPromptSubmit` hooks that DO
inject dynamic text into the conversation — this repo is not a purely
static-doctrine shop:

- `hooks/handoff-resume/resume-check.sh` (SessionStart) — injects a
  pointer to `resume-handoff` only when a `HANDOFF.md` file is actually
  found; silent (empty stdout, exit 0) otherwise.
- `hooks/plugin-staleness/staleness-check.sh` (SessionStart) — injects a
  version-skew warning only when the installed plugin version is
  confirmed strictly behind the source manifest's version; silent
  otherwise.
- `hooks/session-refresh/refresh-check.sh` (UserPromptSubmit) — injects a
  "write a handoff and end" directive only when the session's measured
  re-prime count or p90 context size crosses a budget, read fresh from
  `agentprof` on every prompt; silent otherwise.

All three share a shape the prompt-improver plugin did not: each fires
conditionally on genuinely time-varying state (a file's existence, an
installed version string, a live profiler read) that cannot be known at
system-prompt-authoring time, each is silent (no injected text at all)
when that state hasn't changed, and each injects a single short directive
— never a stacked, always-on wrapper duplicating other content. Nothing in
`.claude/rules/` currently states this pattern as a rule; it exists only
as three independently-converged implementations. A future hook author
has no written guidance distinguishing "this belongs in a conditional
hook" from "this belongs in CLAUDE.md/a rule file," and could easily
reproduce the prompt-improver shape (an always-fires, static-content
nudge) without realizing it's the same anti-pattern already caught once
this session.

## Non-goals

- **Re-litigating or further remediating the `prompt-improver` plugin
  itself.** It is already disabled; whether to uninstall it entirely,
  file an issue upstream, or leave it disabled-but-installed is a
  separate user decision this spec does not make.
- **Building a mechanical lint/gate that inspects hook output for
  "staticness."** Detecting whether a hook's injected text is genuinely
  state-dependent vs. a disguised static nudge is a judgment call a
  reviewer makes reading the hook's source, not something a script can
  reliably classify (a hook can gate on a trivial always-true condition
  to fake conditionality). This spec is doctrine-only, matching how this
  repo's other token-discipline additions (e.g.
  `specs/context-blowout-subagent-guards`) landed as prose bullets, not
  tooling.
- **Auditing or changing third-party plugins other than `prompt-improver`**
  for the same anti-pattern. Out of scope; a human can re-run this
  spec's reasoning against any other installed plugin later if one is
  suspected.
- **Changing any of the three existing hooks' behavior.** The research
  and repo scout both confirm they already follow the recommended
  pattern; this spec's job is to write that pattern down, not modify
  working code.
- **A broader survey of prompt-caching mechanics, context-window sizing,
  or agent-harness architecture** beyond what's needed to answer the
  narrow question this spec opens with. Deeper caching optimization (e.g.
  restructuring this repo's own skill-invocation prompts for better cache
  hit rates) is a separate, not-yet-scoped idea.

## Solution

Add one new bullet to `.claude/rules/token-discipline.md`'s existing
"Cache economics" section (chosen over a new section or new file: the
section already states the static-vs-dynamic cache-cost distinction this
bullet extends, and the repo's authoring convention prefers bullets inside
an existing section over a new header when the topic fits — see the
`context-blowout-subagent-guards` spec's identical choice for a
structurally similar addition). The bullet states the rule this session's
finding makes concrete:

> A hook (`SessionStart`, `UserPromptSubmit`, or any other injection
> point) earns its per-turn cost only when its injected content is
> genuinely time-varying — state that cannot be known at
> prompt-authoring time (a file's live existence, a measured metric, an
> installed version) — and it must be silent (no injected text) when that
> state hasn't changed. A reminder that would read the same on every turn
> belongs in CLAUDE.md or a `.claude/rules/` file instead, where it's
> written once and cached, not repeated. `hooks/handoff-resume/`,
> `hooks/plugin-staleness/`, and `hooks/session-refresh/` are this repo's
> working examples of the former; the disabled `prompt-improver` plugin
> (docs/memory or session history — an always-fires, static-nudge wrapper
> that duplicated prompt text on every single `UserPromptSubmit`) is the
> latter, uncaught until this session.

This is the spec's only concrete action. The research does not support
inventing new dynamic-injection tooling for this repo — the three
existing hooks already demonstrate the correct pattern in working code,
and the gap is purely that nothing written down explains _why_ they're
correct or what to avoid repeating. Per the task brief's own framing,
this is the valid "explicitly document why we don't do X" outcome: the
concrete "X" here is "static, always-fires prompt nudges," and the fix is
one doctrine bullet, not a new mechanism.

No skill file, agent definition, or mirror-path (`antigravity/`, `codex/`)
change: `.claude/rules/` has no mirrored counterpart under `antigravity/`
(confirmed by the same absence noted in
`specs/context-blowout-subagent-guards/SPEC.md`'s R4), so the CLAUDE.md
mirror-obligation note does not apply.

## Requirements

- **R1**: `.claude/rules/token-discipline.md`'s "Cache economics" section
  (currently three bullets, lines ~244–255) gains one new bullet stating
  the rule in the Solution section above: dynamic injection is justified
  only for genuinely time-varying, state-dependent content; a hook must be
  silent when nothing changed; and repeated static reminders belong in
  CLAUDE.md/rules instead. The bullet names `hooks/handoff-resume/`,
  `hooks/plugin-staleness/`, and `hooks/session-refresh/` as this repo's
  compliant examples.
- **R2**: The new bullet cites (name + URL, inline) at least one of the
  research sources from the Problem section — Anthropic's context-rot
  guidance, the prompt-caching hit-rate finding, or the Claude Code hooks
  docs' "time-sensitive information" framing — rather than asserting the
  rule as unsourced opinion.
- **R3**: No other section of `token-discipline.md` is restructured;
  `grep -c "^## " .claude/rules/token-discipline.md` returns the same
  count as before this change (8 sections today — confirmed via
  `grep -n "^## " .claude/rules/token-discipline.md` during this spec's
  authoring).
- **R4**: The bullet does not restate the existing three "Cache economics"
  bullets' content (static-content-at-front, mid-session-edit
  invalidation, tool-set-churn) — it extends the section with a distinct,
  new point about hook-based injection specifically, per this repo's
  cite-don't-restate convention.

## Acceptance signals

- `grep -c "genuinely time-sensitive\|genuinely time-varying" .claude/rules/token-discipline.md`
  → ≥ 1 (currently 0 for both phrasings, re-verified 2026-07-19; confirms
  R1 landed with this or an equivalent literal anchor — adjust the exact
  phrase during breakdown if wording changes, keeping the anchor check in
  sync). Depth ceiling: doctrine prose for future hook authors — deeper
  is infeasible in scope (Non-goals reject a mechanical staticness lint);
  behavioral complement is the MANUAL reviewer read below.
- `grep -c "silent when nothing changed\|silent when that state hasn't changed" .claude/rules/token-discipline.md`
  → ≥ 1 (currently 0, re-verified 2026-07-19; confirms the silence
  requirement landed, not just the general "dynamic is OK" framing).
  Depth ceiling: same as above — behavioral complement is the MANUAL
  reviewer read below.
- `grep -c "hooks/handoff-resume" .claude/rules/token-discipline.md` → ≥ 1
  and `grep -c "hooks/plugin-staleness" .claude/rules/token-discipline.md`
  → ≥ 1 and `grep -c "hooks/session-refresh" .claude/rules/token-discipline.md`
  → ≥ 1 (confirms the bullet names this repo's own compliant hooks as the
  worked examples, not just an abstract rule; anchors are the `hooks/...`
  path forms R1 mandates because the original bare `session-refresh` grep
  was vacuous — the file's "## Session refresh" section already matches
  it twice today; all three path forms verified absent, 0 matches each,
  2026-07-19). Depth ceiling: same as above — behavioral complement is
  the MANUAL reviewer read below.
- `grep -n "^## Cache economics" .claude/rules/token-discipline.md`
  returns exactly one match (section not duplicated or renamed).
- `grep -c "^## " .claude/rules/token-discipline.md` → 8 (R3's count
  check; verify against `git show HEAD:.claude/rules/token-discipline.md
| grep -c '^## '` at breakdown time in case another spec lands first).
- MANUAL: a human or reviewing agent reads the new bullet and confirms it
  cites at least one named, URL-backed source (R2) and does not duplicate
  the section's existing three bullets (R4).

Next stage: /critique specs/prompt-tweaking-roi/SPEC.md (human-launched,
or self-chain if the live request explicitly asks for it).
