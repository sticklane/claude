# Handoff — ctx improvement round 2: CUJs + indexing fixes (2026-07-21)

Written at Steven's direction under a context-budget refresh. Start the
fresh session in `~/claude`. Everything below is self-contained.

## What the previous session shipped (all committed + pushed)

A ctx-driven codebase survey of fooszone produced six fooszone specs
(all critiqued; 5 READY, mllive-decomposition intentionally
Breakdown-ready: false) and four ~/claude specs, all critiqued READY
except where noted:

- `specs/ctx-skill-token-doctrine` — triggering, reading ladder,
  survey model-tiering, scout `Bash(ctx *)` grant, absence-fallacy
  scope caution (R7). READY.
- `specs/ctx-static-analysis-augmentation` — LSP exactness (F1),
  clone detection (F2), ast-grep rung. Fork-gated R2/R3; R1/R4/R5
  breakable after token-doctrine R2.
- `specs/ctx-query-ergonomics` — file-scoped selectors, `ctx show`,
  `--in/--not-in` filters. READY WITH NITS applied
  (critique-findings.md records).
- `specs/shell-text-tool-doctrine` — sed/awk/grep alignment. READY,
  not yet critiqued by an agent (authored from research).

Research grounding gathered: Aider repo map (token-budgeted,
reference-ranked signatures); Codebase-Memory arXiv 2603.27277 (10×
fewer tokens, 2.1× fewer tool calls at 83% vs 92% quality → escalation
ladder, not index-only); Serena/LSP 3.17 call-type hierarchy as the
precision layer; claude-code issue #21697 + SWE-agent ACI (bounded
output, dedicated tools over sed -i).

## Steven's new directives (2026-07-21, verbatim intent)

1. **Minified JS must not be processed at all.** Not a membership
   question (.ctxignore) — an INDEXER capability: detect minified
   content (e.g. `.min.js`/`.min.css` naming, single-line ratio,
   extreme avg line length, symbol-density explosion) and skip
   parsing, with a visible "skipped: minified" marker in tree/map
   output. fooszone evidence: root `paper-full.min.js` made `ctx map`
   ~90% noise.
2. **Dead code is GOOD to find — do not blanket-exclude it.** This
   REVERSES part of the prior framing: `attic/` hits in refs
   (lerp/rodSpecs duplicates) were treated as pollution, but Steven
   wants dead-code discovery as a first-class outcome. Design: keep
   archived/dead trees indexed but ZONED — results tagged (e.g.
   `[attic]`/`[archived]` on the path, configurable zone globs),
   filterable via the already-specced `--in/--not-in`, default-visible
   with the tag. Consequence: AMEND fooszone
   `specs/repo-orientation-hygiene` R3 — `.ctxignore` should list
   `vendor/` + `dist/` only, NOT `attic/` (attic stays indexed,
   zoned). Also consider a dead-code CUJ: "what's defined but only
   referenced from dead zones."
3. **Fix the absence fallacy IN THE TOOL** (doctrine caution already
   landed in token-doctrine R7, but Steven wants the tool fixed): a
   no-match `refs`/`sig` result must state the boundary ("no symbol —
   object fields, JSON keys, and string literals are not indexed")
   and offer/perform a bounded content-check fallback (design choice:
   print a suggested `grep -rl` vs run it capped vs a `ctx text
<string>` subcommand). Live failure it prevents: the figureBboxes
   false-absence claim (2026-07-20).
4. **Canonical dig-in path**: `ctx show` + file-scoped selectors
   (ctx-query-ergonomics) is the intended answer — verify it covers
   "dig into things" end-to-end (locate → disambiguate → show →
   edit), extend that spec rather than duplicating.
5. **Define the CUJs.** Given the research + findings, write the
   canonical critical-user-journey set for ctx and derive gaps.
   Candidate list to refine: ORIENT (map/tree on a clean index);
   LOCATE (refs/sig with disambiguation); DIG IN (show); VERIFY
   ABSENCE (symbol + content fallback — new); IMPACT (refs, later
   --exact via LSP); SURVEY (batched recipe → cheap-tier scout);
   DEDUP/DEAD-CODE (clone detection + zone-only-referenced query —
   new); KNOWLEDGE (notes). Each CUJ: trigger, query sequence, token
   budget, failure modes. Home: `specs/ctx-cujs/SPEC.md` (or a doc
   under specs/codebase-context-tree/ if it fits better as the
   umbrella's doctrine) — CUJs then become the acceptance frame for
   the other ctx specs.

## Next step (do this first)

1. Write the new specs in `~/claude/specs/`: `ctx-minified-skip`,
   `ctx-dead-code-zones` (subsumes the attic reframe + amends
   ctxignore-git-overlay's scope note if needed), `ctx-absence-check`
   (tool-side), `ctx-cujs` (the CUJ doctrine). Cross-reference the
   existing four ctx specs; keep landing-order constraints consistent
   (SKILL.md is a shared merge surface — see token-doctrine's Landing
   order section).
2. Amend fooszone `specs/repo-orientation-hygiene` R3 per directive 2
   (drop attic from .ctxignore; note the zoning spec). Commit with
   pathspecs (shared checkout rules in fooszone CLAUDE.md).
3. Critique everything: NOTE — the agentic plugin's skills/agents
   (critic, scout, /critique, /handoff) went UNAVAILABLE at the end of
   the prior session (plugin cache changed mid-session; `Skill:
agentic:critique` worked earlier, then `Unknown skill`). Check
   `claude plugin list --json` first; if still absent, author the
   critic dispatch manually as a general-purpose Agent with the
   adversarial-review framing used in specs/*/critique-findings.md.
4. Commit + push ~/claude after each spec; delete this HANDOFF.md when
   consumed.

## State / gotchas

- Both repos clean of session work and pushed: ~/claude at 71a95cf,
  fooszone at 07dbc2d6. fooszone tree has pre-existing dirt not ours
  (.claude/scheduled_tasks.lock, eval clip mtime).
- Monthly API spend limit was hit early on 2026-07-20 (subagents died)
  then evidently lifted (critics ran later). If subagents fail with
  spend-limit errors, tell Steven — claude.ai/settings/usage.
- A PostToolUse formatter reflows .md on Write/Edit in both repos —
  re-check `git diff` before path-scoped commits.
- fooszone memory `feedback-ctx-skill-triggering.md` records the
  session's ctx lessons; MEMORY.md was compacted (two new topic files).
