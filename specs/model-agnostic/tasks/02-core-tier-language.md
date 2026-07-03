# Task 02: Core prose to tier language with fallback-safe citations

Status: pending
Depends on: 01
Budget: 30 turns
Spec: ../SPEC.md (requirements R2, R3, R4, R5 (citations), R9)

## Goal

De-Claude the core prose: scout.md and exactly two prose files adopt
"scout-tier" language with the Claude default named inline, the drain and
autopilot headless templates get an "active runtime profile" framing
sentence (templates themselves unchanged), and README/CLAUDE.md gain the
runtime-selection pointers. Every citation of `runtimes/` from
plugin-shipped files must carry the fallback clause (absent in plugin
installs and eval fixtures → claude-code defaults apply).

## Touch

- .claude/agents/scout.md
- .claude/rules/token-discipline.md
- README.md
- .claude/skills/autopilot/reference.md
- .claude/skills/gate/reference.md
- .claude/skills/drain/reference.md
- CLAUDE.md
- Cross-spec: also edited by review-fixes, context-management, chaining-antipatterns, beads-integration — see specs/QUEUE.md

## Steps

1. `.claude/agents/scout.md`: keep `model: haiku` in frontmatter; add a
   body line naming its tier, phrased fallback-safe per R2: "scout-tier —
   mapping for other runtimes in `runtimes/` (toolkit repo; absent in
   plugin installs and eval fixtures, where the claude-code defaults
   above apply)". Do not touch critic.md or verifier.md.
2. `.claude/rules/token-discipline.md`: convert both Haiku mentions to
   tier language with the Claude default in parentheses, using
   "scout-tier" verbatim — the scout definition (~line 10) and the
   model-matching bullet (~line 21: "Mechanical or lookup work →
   scout-tier (Claude default: Haiku at low effort)").
3. `README.md`: convert the scout table row and the token-cost bullet to
   the same tier-plus-inline-default phrasing (these are the other two of
   the four Haiku mentions R3 covers — no others change).
4. `.claude/skills/autopilot/reference.md` and
   `.claude/skills/gate/reference.md`: reword their `/goal` transcript
   evaluator Haiku lines as "the runtime's built-in transcript evaluator
   (Claude Code: Haiku)" — these are NOT tier vocabulary; the word
   "scout-tier" must not appear in either file.
5. `.claude/skills/drain/reference.md` and
   `.claude/skills/autopilot/reference.md`: introduce each headless
   command template with one sentence containing the phrase "active
   runtime profile" — the template below is the Claude Code profile's
   rendering; other runtimes substitute their profile's `## Headless`
   template. Cite `runtimes/README.md` for selection (do not restate the
   convention) with the R5 fallback clause: the directory lives in the
   toolkit repo, is absent in plugin installs and eval fixtures, and its
   absence means the claude-code defaults apply. Leave the concrete
   `claude -p` blocks byte-identical.
6. `README.md`: add a short "Other runtimes and models" subsection under
   Install: Claude models are the default; select another runtime via
   `.claude/runtime.md` + `runtimes/`; porting guide at `docs/porting.md`.
7. `CLAUDE.md`: add one conventions bullet: "concrete model names and CLI
   command templates appear in core files only as the inline Claude
   default; the mappings for other runtimes live in `runtimes/` profiles
   — new skills use tier language plus the inline default, never a bare
   model name."
8. Do NOT bump `.claude-plugin/plugin.json` — the single batch version
   bump (R10) is owned by global task 99 in specs/review-fixes.

## Acceptance

- `grep -q "scout-tier" .claude/agents/scout.md && grep -q "model: haiku" .claude/agents/scout.md && grep -qi "absent in plugin installs" .claude/agents/scout.md` → exit 0 (R2)
- `grep -q "scout-tier" .claude/rules/token-discipline.md && grep -q "scout-tier" README.md` → exit 0 (R3)
- `grep -qi "built-in transcript evaluator" .claude/skills/autopilot/reference.md && grep -qi "built-in transcript evaluator" .claude/skills/gate/reference.md && ! grep -qi "scout-tier" .claude/skills/autopilot/reference.md && ! grep -qi "scout-tier" .claude/skills/gate/reference.md` → exit 0 (R3 — evaluator lines reworded, no tier mislabel)
- `grep -q "active runtime profile" .claude/skills/drain/reference.md && grep -q "active runtime profile" .claude/skills/autopilot/reference.md && grep -q "claude -p" .claude/skills/drain/reference.md` → exit 0 (R4)
- `grep -q "absent in plugin installs" .claude/skills/drain/reference.md && grep -q "absent in plugin installs" .claude/skills/autopilot/reference.md` → exit 0 (R5 fallback clauses in the plugin-shipped citers)
- `grep -qi "Other runtimes" README.md && grep -q "runtimes/" CLAUDE.md` → exit 0 (R9)
