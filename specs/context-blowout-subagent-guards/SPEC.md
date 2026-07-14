Status: open
Priority: P2
Breakdown-ready: true

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

**`/workboard`'s "Relay the inbox" step pulls raw cross-repo scan output
directly into the orchestrating session.** A live `/agentic:workboard` run
across 5 repos (`~/automation`, `~/claude`, `~/fooszone`, `~/hub`,
`~/interview-prep`) returned 69 needs-attention items. The skill's own step
2 instructs the orchestrator to run
`python3 <skill dir>/workboard.py --json` itself, in its own Bash tool
call, then parse and summarize that JSON in its own turn — there is no
delegation step, unlike `token-discipline.md`'s general "Delegation
defaults" principle ("Never read files into main context to 'look
around'... use the scout agent for any where/how/what-exists question").
The result: potentially unbounded per-repo JSON (69 items this run, more in
a busier week) lands in the orchestrating session's own context before any
summarization happens — the same "documented practice exists elsewhere,
not reinforced at the point of use" shape as the two gaps above, just for
a different tool (a repo-owned skill, not a third-party plugin) and a
different resource (a scanner's stdout, not browser screenshots).

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
   (`scout` has no MCP tool grant per `.claude/agents/scout.md` — its
   frontmatter lists `Read, Grep, Glob, Bash(git log *), Bash(git show *),
Bash(ls *), Bash(wc *)` only — and so cannot drive
   `mcp__claude-in-chrome__*` tools).

   Both edits (this one and the "Dispatch authoring" bullet below) land in
   `.claude/rules/token-discipline.md`; they ship as a single breakdown
   task rather than two, since two same-file-`Touch` tasks cannot be
   drained in parallel.

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

3. **`/workboard`'s "Relay the inbox" step** (`.claude/skills/workboard/SKILL.md`,
   step 2) is rewritten so the orchestrating session never runs
   `workboard.py --json` (or the fallback scanner) directly: it dispatches
   a `scout`-tier subagent to run the scan and return only the curated
   needs-attention summary (capped items per repo, with an explicit "N more
   not shown, see the live dashboard" line when the cap truncates anything —
   token-discipline.md's "no silent caps" rule, cited not restated). One new
   bullet in `token-discipline.md`'s "Delegation defaults" section states
   the general form (route a multi-repo/multi-item scanner's raw output
   through a subagent before it reaches the orchestrating session, same
   shape as the browser-screenshot and deferred-tool bullets above), and
   the `/workboard` SKILL.md step cites that bullet rather than restating
   it — keeping both edits minimal (a pointer plus the delegation
   instruction, not a rewritten step) so this fix does not itself add to
   the global-context bloat it's fixing; `token-discipline.md` and
   `/workboard`'s `SKILL.md` are both already-loaded-every-session /
   already-loaded-on-invocation files, so their net addition should stay a
   few lines, matching this repo's own existing "cite, don't restate"
   convention for rule and skill content.

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

> "[a live `/agentic:workboard` run] total inbox items: 69 ... by repo:
> {'hub': 23, 'fooszone': 20, 'claude': 14, 'automation': 10, 'specs': 2}"
> — the full JSON backing this summary was piped through the orchestrating
> session's own Bash tool call (`workboard.py --json`), not a subagent, so
> all 69 items' raw content entered the session's context before any
> filtering happened.

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
  than add an unnecessary mirror step. (R4 applies only to R1–R3; R5–R8
  below DO touch a skill file, by design — see R6.)
- **R5**: `.claude/rules/token-discipline.md`'s "Delegation defaults"
  section gains a new bullet (after the R1/R2 bullets, before `## Model and
effort matching`) requiring any skill that scans multiple repos or
  returns a multi-item/unbounded result set (naming `/workboard` as the
  evidenced case) to route the raw scan through a subagent — never run the
  scanner directly in the orchestrating session and parse its output there
  — and to cap the relayed summary with an explicit "N more not shown"
  line when truncating (citing this same section's existing "no silent
  caps" principle, not restating it).
- **R6**: `.claude/skills/workboard/SKILL.md`'s step 2 ("Relay the inbox")
  is rewritten to dispatch a `scout`-tier subagent that runs
  `workboard.py --json` (or the fallback scanner) and returns only the
  curated, capped needs-attention summary — the orchestrating session
  never invokes the scanner directly. The live-dashboard step (step 1) is
  unchanged: it already runs server-side and costs the orchestrating
  session nothing.
- **R7**: `antigravity/`'s workboard mirror (if one exists covering the
  "Relay the inbox" step) is updated to match, per this repo's
  mirror-procedure-discipline rule (cited, not restated) — confirm at
  breakdown time whether `antigravity/.agents/skills/workboard/` mirrors
  this specific step or only the dashboard-launch step.
- **R8**: Both R5 and R6's edits stay minimal — a pointer bullet plus the
  delegation instruction, not a rewritten section — so fixing this
  context-cost problem does not itself add meaningfully to the
  already-loaded-every-session (`token-discipline.md`) or
  already-loaded-on-invocation (`workboard/SKILL.md`) file sizes; net new
  lines in each file should be small enough to eyeball at code review, no
  numeric line cap needed beyond that judgment call.

## Out of scope

- Editing the `claude-in-chrome` plugin's own bundled MCP-server
  instructions (external, not owned by this repo).
- Changing the harness's per-session deferred-tool system-reminder
  mechanism (harness-level, outside this repo's control).
- Building tooling to enforce the screenshot cap mechanically (a hook,
  a lint check); this spec is doctrine-only, matching how the existing
  `large-codebase-context-guide` precedent bullet was landed.
- Any change to `.claude/agents/scout.md`'s tool grant.
- The live dashboard's own HTML/CSS/JS rendering, readability, or UX/visual
  design (a separately-requested task) — R6 touches only the SKILL.md's
  chat-relay step, never the dashboard-launch step or its frontend code.
- Applying the same subagent-delegation fix to `/list-specs` or
  `/prioritize`, which scan similarly but were not the evidenced incident —
  worth a follow-up spec if either is found to have the same unbounded-dump
  shape, not bundled into this one.
- Any change to `.claude/agents/scout.md`'s tool grant for R5–R8 either
  (same constraint as R1: `scout` already has the `Bash`/`Read`/`Grep`/
  `Glob` grant a JSON-scanning-and-summarizing task needs).

## Acceptance criteria

- `grep -c "route each page-check through a subagent" .claude/rules/token-discipline.md` → 1 (currently 0; confirms R1's bullet landed with this or an equivalent literal anchor — adjust the exact phrase during breakdown if wording changes, keeping the anchor check in sync).
- `grep -c "2 direct-context screenshots" .claude/rules/token-discipline.md` → 1 (currently 0; confirms R1(b)'s concrete cap landed, not just the delegation requirement in R1(a) — adjust the exact phrase during breakdown if wording changes, keeping the anchor check in sync).
- `grep -c "batch-load the tool's schema via" .claude/rules/token-discipline.md` → 1 (currently 0; confirms R2's bullet landed — adjust the exact phrase during breakdown if wording changes, keeping the anchor check in sync).
- `grep -n "^## Delegation defaults" .claude/rules/token-discipline.md` and `grep -n "^## Dispatch authoring" .claude/rules/token-discipline.md` each still return exactly one match (sections not duplicated or renamed).
- `grep -c "^## " .claude/rules/token-discipline.md` returns the same count as before the change (8 sections; new content is bullets inside existing sections, not new headers) — verify against `git show HEAD:.claude/rules/token-discipline.md | grep -c '^## '` at breakdown time.
- MANUAL: a human or reviewing agent reads both new bullets in context and confirms they cite rather than restate the RETRY evidence and the `scout` tool-grant constraint, per R3.
- `grep -c "route the raw scan through a subagent" .claude/rules/token-discipline.md` → 1 (currently 0; confirms R5's bullet landed).
- `grep -c "scout\`-tier subagent" .claude/skills/workboard/SKILL.md` → ≥ 1 (currently 0; confirms R6's rewrite landed — adjust the exact phrase during breakdown if wording changes).
- `grep -n "^## " .claude/skills/workboard/SKILL.md` shows the same section count and titles as before this spec's change (step 2 content changed, no section added/removed/renamed) — verify against `git show HEAD:.claude/skills/workboard/SKILL.md | grep -n '^## '` at breakdown time.
- MANUAL-PENDING: a human or a reviewing agent invokes `/workboard` in a repo with a large synthetic inbox (or this repo's own current inbox) and confirms, by reading the orchestrating session's own tool-call history, that no raw scanner JSON output appears in the orchestrator's own Bash tool result — only the subagent's capped summary does. An unattended worker cannot self-certify this (it would need to observe its own context from outside), so this is left MANUAL-PENDING per `.claude/rules/mirror-verification.md`'s escape clause, cited not restated.

## Parallelization

This spec decomposes into a single task (01) for R1–R4 — both R1 and R2
edits share one `Touch` target (`.claude/rules/token-discipline.md`), so
they cannot be split into concurrent-safe groups per the decision-coupling
test; no `- Group:` line applies.

R5–R8 need a second task: R5 shares `token-discipline.md` with task 01 (same
file — sequential, not concurrent, whichever task lands second must not
stomp the other's diff), while R6/R7 touch `.claude/skills/workboard/SKILL.md`
(and possibly its `antigravity/` mirror) — a disjoint `Touch` set from task
01's file, but still bundled with R5 into one task since R5/R6 are one
conceptual change (the doctrine bullet and the skill fix that cites it ship
together, matching how R1/R2 already ship as one task above). Breakdown
should decide: fold R5–R8 into task 01 (if task 01 hasn't been dispatched
yet) or add task 02 with `Depends on: 01` (if task 01 is already in flight)
— see Open questions.

## Open questions

- The 2-screenshots-per-turn cap is this spec's proposed anchored default,
  chosen as a small concrete number per the task brief's own suggestion
  (1–2); a human may want a different number based on how the actual
  `claude-in-chrome` skill/workflow gets built out later.
- Whether R5–R8 fold into existing task 01 or become a new task 02
  (`Depends on: 01`) depends on task 01's `Status:` at breakdown time —
  check `specs/context-blowout-subagent-guards/tasks/01-token-discipline-bullets.md`
  before deciding; this spec does not resolve it, since it may change
  between this spec's authoring and its next breakdown/critique pass.
- If a future spec adds a dedicated `claude-in-chrome`-usage rule file or
  skill section to this repo (none exists today), this spec's R1 bullet
  should be migrated there rather than left permanently in
  `token-discipline.md`'s general "Delegation defaults" section — noting
  this now so it isn't lost.
