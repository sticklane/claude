# Context-management learnings: compaction, memory, cache economics

## Problem

Fresh cross-vendor research (Anthropic's context-engineering post and
Claude Code docs; ADK's sessions/memory whitepaper; OpenAI's caching and
prompting guides — recorded by this spec in docs/external-playbooks.md)
confirms the toolkit's core context model but exposes five gaps: nothing
steers what compaction preserves when a session auto-compacts mid-queue;
skill bodies truncate post-compact and our SKILL.md files don't
front-load their critical instructions; the toolkit has no agent-written
cross-task memory (only human-triggered /distill); nothing teaches cache
economics (static-first structure; mid-session CLAUDE.md churn and
tool-set changes invalidate prompt caches); and only the scout agent has
a numeric tool-call ceiling. One convention gap ties directly to a
standing review finding: machine-read state must live in header lines,
not body prose (the Touch-in-body defect class).

## Solution

Four decisions, recommended options adopted (interview picker unavailable
this session — 3/3 stream failures — so the skill's non-interactive
fallback applies; each reversible before implementation): (1) /distill
gains a lightweight agent-maintained memory layer — a `docs/memory.md`
index (≤200 lines) plus topic files, written by the agent when lessons
don't fit CLAUDE.md; (2) compaction steering lives in a "Compact
instructions" section of CLAUDE.md (the location Claude Code honors);
(3) numeric tool-call ceilings extend to the critic and verifier agent
definitions; (4) the machine-state-in-headers rule is stated in
CLAUDE.md's conventions and /breakdown's template note — the actual
relocation of `Touch` into a header line is owned by the code-review fix
wave, not this spec (coordination note in Out of scope). Marker phrases
("Compact instructions", "docs/memory.md", "tool-call ceiling",
"static-first") do not exist in the repo today.

## Requirements

- R1 (compaction steering): CLAUDE.md gains a `## Compact instructions`
  section (≤10 lines) telling compaction what to preserve for this
  toolkit's work: task-file paths and their Status values, the current
  wave/dispatch state, branch names, acceptance-evidence pointers, and
  unresolved review findings — and what to drop first (raw tool output,
  file listings). CLAUDE.md stays ≤200 lines total after the addition.
- R2 (post-compact skill survival): CLAUDE.md's authoring conventions
  gain: SKILL.md files put execution-critical contracts in the first 30
  lines (skill bodies truncate when a session compacts; descriptions
  reload, bodies do not); reference files over 100 lines open with a
  table of contents; references stay one level deep. Every reference
  file currently over 100 lines gains a TOC to comply: drain (205),
  fleet (182), gate (167), autopilot (110), evals (110).
- R3 (agent-written memory): `.claude/skills/distill/SKILL.md` gains a
  memory-layer step: lessons that are too narrow or too long for
  CLAUDE.md go to a topic file under `docs/memory/`, indexed in
  `docs/memory.md` (agent-maintained, ≤200 lines, one line per topic
  file: path + when-to-read trigger phrase). The index is loaded on
  demand, never at session start; /distill prunes stale entries when it
  writes (semantic decay, manual-trigger version). The skill states the
  artifact locations and that CLAUDE.md remains the home for always-on
  rules. So the layer is ever READ: CLAUDE.md gains one always-on
  pointer line — "narrow per-topic lessons are indexed in
  `docs/memory.md`; check it when a task matches a topic" — within R1's
  line budget.
- R4 (cache economics): `.claude/rules/token-discipline.md` gains a
  short "Cache economics" section containing the phrase "static-first":
  stable content (rules, skill text, unchanged files) belongs at the
  front of prompts and must not churn mid-session; CLAUDE.md/rules edits
  invalidate the cached prefix — /distill therefore batches CLAUDE.md
  writes at session end (one matching sentence added to
  `.claude/skills/distill/SKILL.md`); tool-set changes bust caches — don't
  add/remove MCP servers or edit agent `tools:` lists mid-run
  (harness-managed deferred tool loading is fine and outside this
  rule).
- R5 (tool-call ceilings): `.claude/agents/critic.md` and
  `.claude/agents/verifier.md` gain a numeric tool-call ceiling line
  (the phrase "tool-call ceiling"; ~25 for critic with scout-style
  best-effort reporting). The verifier's ceiling (~20) EXEMPTS
  per-criterion acceptance commands from the count (it must exercise
  every criterion), and on hitting the ceiling its verdict is
  INCOMPLETE — never PASS — listing the unexercised criteria. The
  verifier's output-contract line becomes "Verdict line: `PASS` /
  `FAIL` / `INCOMPLETE`" in BOTH `.claude/agents/verifier.md` and
  `antigravity/.agents/skills/verifier/SKILL.md`. Caller files
  (autopilot, build, drain) are deliberately NOT edited: their existing
  routing treats anything non-PASS as not-passed (drain ranks "PASSing
  survivors"; autopilot's non-PASS branch reports), so INCOMPLETE is
  non-PASS by construction. Runaway exploration gets a stop without
  ever letting partial evidence pass a gate.
- R6 (machine-state convention): CLAUDE.md's authoring conventions gain
  one bullet: fields any skill reads programmatically (Status, Depends
  on, Budget, and — after the review fix wave — Touch) are single-line
  `Key: value` headers above the first `##` heading of the file; body
  sections are for humans and workers, never for orchestrator parsing.
  `/breakdown`'s template gains a one-line comment stating the same.
- R7 (research record): `docs/external-playbooks.md` gains a "Context
  management" section: what was adopted (R1–R6 mapped to sources), what
  was already covered (attention budget, JIT retrieval, subagent
  isolation with the 1,000–2,000-token summary validation of scout
  budgets, progressive disclosure), where the toolkit leads (tool-result
  size discipline — no vendor guidance found), and what was deliberately
  skipped (ADK scope tiers, artifact versioning, OpenAI
  verbatim-minus-tools handoffs — with one-line reasons), with source
  links.
- R8 (mirrors): `antigravity/AGENTS.md` mirrors R4's cache-economics
  section and R6's convention (its token-discipline content lives
  there); the antigravity distill skill mirrors R3's memory step;
  scout/critic/verifier ceiling mirrors go to
  `antigravity/.agents/skills/{critic,verifier}/SKILL.md`.
- R9 (versioning): the implementing change bumps `plugin.json`'s minor
  version by one from the value it finds, unless landing in a commit-set
  whose other specs already carry a single combined bump.

## Out of scope

- Relocating `Touch` to a header line or any other drain/breakdown
  parsing change — owned by the code-review fix wave (review finding on
  drain's inventory contract); R6 only states the convention that fix
  implements. If this spec lands first, R6's bullet simply predates its
  enforcement.
- Harness-level features: context-editing API beta, auto-memory,
  auto-compact thresholds — the toolkit documents and steers them; it
  cannot implement them.
- Tool-response shaping for consumer projects (response_format enums,
  pagination) — recorded in R7's research entry only; our agent report
  formats already carry budgets.
- A NOTES.md-per-task pattern — task files already fill that role.
- Numeric ceilings for main-session tool use (ceilings are for
  fan-out agents whose transcripts are discarded).

## Acceptance criteria

- [ ] `grep -q "^## Compact instructions" CLAUDE.md && test "$(wc -l < CLAUDE.md)" -le 200` (R1)
- [ ] `grep -qi "first 30 lines" CLAUDE.md && grep -qi "table of contents" CLAUDE.md` (R2 conventions)
- [ ] `for f in .claude/skills/*/reference.md; do [ "$(wc -l < "$f")" -le 100 ] || head -5 "$f" | grep -qi "contents\|TOC" || exit 1; done` — every >100-line reference file opens with a TOC (R2)
- [ ] `grep -q "docs/memory.md" .claude/skills/distill/SKILL.md && grep -qi "stale" .claude/skills/distill/SKILL.md && grep -q "docs/memory.md" CLAUDE.md` (R3)
- [ ] `grep -q "static-first" .claude/rules/token-discipline.md && grep -qi "session end" .claude/skills/distill/SKILL.md` (R4)
- [ ] `grep -q "tool-call ceiling" .claude/agents/critic.md && grep -q "tool-call ceiling" .claude/agents/verifier.md && grep -q "INCOMPLETE" .claude/agents/verifier.md && grep -q "INCOMPLETE" antigravity/.agents/skills/verifier/SKILL.md` (R5)
- [ ] `grep -qi "single-line" CLAUDE.md && grep -qi "header" .claude/skills/breakdown/SKILL.md` (R6)
- [ ] `grep -qi "context management" docs/external-playbooks.md && grep -qi "tool-result size" docs/external-playbooks.md` (R7)
- [ ] `grep -q "static-first" antigravity/AGENTS.md && grep -q "tool-call ceiling" antigravity/.agents/skills/critic/SKILL.md && grep -q "tool-call ceiling" antigravity/.agents/skills/verifier/SKILL.md && grep -q "docs/memory.md" antigravity/.agents/skills/distill/SKILL.md` (R8)
- [ ] plugin.json minor version strictly greater than the pre-implementation value, verified in the implementing task's evidence (R9)
- [ ] End to end: in a fresh session, run /distill after a session that produced one narrow lesson; verify it lands as a `docs/memory/` topic file plus one index line in `docs/memory.md` (not a CLAUDE.md edit), and that `wc -l docs/memory.md` ≤ 200 (manual until the eval harness covers /distill).

## Open questions

(none — the four decisions are recorded in Solution; recommended
options adopted per the non-interactive fallback, reversible before
implementation.)
