# ctx skill: triggering, token-efficient reading doctrine, and model tiering

Breakdown-ready: true

## Problem

Live evidence from a fooszone survey session (2026-07-20): the `ctx` skill
failed to auto-trigger on two explicit user prompts — "please use ctx to
understand the codebase deeply" and "use ctx as much as possible, not grep"
— because its description's trigger phrases are all question-shaped
("where is X defined", "what calls X"). The raw CLI was driven via Bash
instead, so the skill's scope cautions and fallback doctrine never loaded.
Separately, the skill and the CLAUDE.md guidance it anchors encode "prefer
ctx over reading files" but not the rest of token-efficient reading
practice: no escalation ladder, no output-hygiene guidance, no
survey-mode recipe, and no policy for when ctx queries should run on a
cheap model instead of the frontier main loop.

Research grounding (docs/codebase-context-tree-research-2026-07.md covers
build-time prior art; this spec adds usage-time evidence):

- Aider's repo map selects reference-ranked identifiers under an explicit
  token budget — structure is delivered as signatures, never bodies
  (aider.chat/2023/10/22/repomap.html).
- Codebase-Memory (arXiv 2603.27277) measures a tree-sitter knowledge
  graph agent at ~10× fewer tokens and 2.1× fewer tool calls than a
  file-exploration agent, at 83% vs 92% answer quality. The implication
  is not "index-only" but an explicit escalation ladder: index-first,
  with defined triggers for escalating to content search and file reads —
  the ~9-point quality gap is exactly the cases where structure alone
  can't answer.
- The same session produced concrete escalation cases: `heuristic`-tagged
  refs with identical qualified paths in two directories
  (`main.rodSpecs` in go/cmd/mlhybrid and attic/go-cmd/mloverlay) that
  `ctx sig` cannot disambiguate; and function-body/string-literal
  questions (hardcoded constants, MCP tool-name registrations) that are
  content questions by construction.

## Solution

Four small, mostly-docs changes: widen the skill's trigger surface, encode
the reading ladder and output hygiene in the skill body, add a survey-mode
recipe with a model-tiering rule (inline for ≤4 targeted queries; delegate
batched surveys to a cheap-tier scout), and propagate the same doctrine to
the CLAUDE.md guidance the toolkit distributes (/onboard template + the
token-discipline rule). No changes to the `ctx` binary.

## Requirements

- R1 — Trigger surface. Extend the skill frontmatter description with
  tool-directive phrasing ("use ctx", "with ctx", "via ctx", "the ctx
  skill", "ctx the codebase") and survey phrasing ("understand the
  codebase", "survey the repo structure", "deep-dive the code structure").
  Keep the existing negative scope ("not for content/text search").
  Acceptance: `grep -c 'use ctx' .claude/skills/ctx/SKILL.md` ≥ 1, and
  each phrase family above appears in the description line. Mirror the
  change to `antigravity/.agents/skills/ctx/SKILL.md` (content-parity
  audit exists: specs/codequality-antigravity-content-parity).

- R2 — Escalation ladder. Add a "Reading ladder" section to the skill
  body prescribing, in order: (1) ctx query; (2) structural content
  search (ast-grep where available, else Grep with `-l` or `-C 0`) when
  the question is about bodies, literals, or patterns; (3) sliced Read
  (`offset`/`limit` around a ctx-reported line) when a specific body must
  be read; (4) whole-file Read only when about to edit. Name the concrete
  escalation triggers observed in practice: symbol not indexed,
  identical-qpath ambiguity, `heuristic` tag on a load-bearing ref,
  body/literal questions. Acceptance: section present; each of the four
  rungs and four triggers named.

- R3 — Output hygiene. Skill body documents: pipe `map`/`tree`/`refs`
  through `head` or use `--limit`/`--json | jq` slices; batch independent
  queries into one shell invocation; never paste more query output into
  conversation than the decision needs. Acceptance: guidance present with
  at least one worked pipe example.

- R4 — Survey mode + model tiering. Add a "Codebase survey" section: for
  whole-repo understanding requests, the recipe is `map --limit N` +
  `tree` per top-level module + `deps` on entry points. Tiering rule: up
  to ~4 targeted queries run inline (delegation overhead exceeds the
  savings); a batched survey or open-ended multi-question exploration is
  delegated to a cheap-tier scout whose prompt embeds the query recipe
  and returns a distilled structure report — the main model never reads
  raw query dumps for surveys. The queries themselves are deterministic
  CLI calls; the model tier only governs whose context absorbs the
  output. Acceptance: section present; contains an explicit dispatch
  prompt template for the scout including the ctx command table.

- R5 — Scout integration. The `scout` agent definition's prompt gains a
  line directing it to prefer `ctx` queries (when the repo is indexed)
  before Grep/Read, so cheap-tier delegation from R4 works without the
  skill needing to trigger inside the subagent. Acceptance: scout
  definition mentions ctx with the binary-resolution one-liner.

- R6 — CLAUDE.md guidance propagation. (a) The /onboard skill's CLAUDE.md
  template emits an "Answering structure questions" section (modeled on
  fooszone's) when the repo has a ctx index, including the reading
  ladder's rung order. (b) The toolkit's token-discipline rule
  (`.claude/rules/token-discipline.md` or equivalent distributed copy)
  names index-first reading as the default for structural questions,
  before scout dispatch. Acceptance: template renders the section for an
  indexed repo; rule file names ctx.

- R7 — Scope cautions currency. Skill scope cautions add: refs/sig
  results are name-resolution heuristics (tagged `heuristic`), not
  compiler-verified — see specs/ctx-static-analysis-augmentation for the
  exactness path; identical-qpath collisions across directories are
  unresolvable via `sig` (fall back to sliced Read); `map` noise from
  committed vendored/generated trees is an index-membership problem fixed
  by specs/ctxignore-git-overlay, not by more querying. Acceptance:
  cautions mention all three.

## Non-goals

- Changing the `ctx` binary or index schema (separate specs own that).
- A skill-triggering eval harness (worthwhile, but belongs to the
  evals/ program; a follow-up task may wire the R1 phrase table into it).

## Evidence

- fooszone memory: `feedback-ctx-skill-triggering.md` (2026-07-20 session).
- Aider repo map: https://aider.chat/2023/10/22/repomap.html
- Codebase-Memory: https://arxiv.org/html/2603.27277v1
