# Task 02: Core prose to tier language with fallback-safe citations

Status: pending
Depends on: 01, ../../review-fixes/tasks/01-plugin-manifest.md, ../../review-fixes/tasks/08-mirrors-and-docs.md
Budget: 30 turns
Spec: ../SPEC.md (requirements R2, R3, R4, R5 (citations), R9, R11)

## Goal

De-Claude the core prose: scout.md and exactly two prose files adopt
"scout-tier" language with the Claude default named inline,
token-discipline's model-matching section becomes the four-rung tier
ladder with the "tier pin" dispatch rule (R11), the drain and
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
2. `.claude/rules/token-discipline.md`: convert the scout definition
   (~line 10) to tier language with the Claude default in parentheses,
   using "scout-tier" verbatim. Then (R11 — this subsumes the old
   line-~21 edit) rewrite the "Model and effort matching" section as a
   four-rung ladder containing the phrase "tier pin": scout-tier for
   mechanical or lookup work (Claude default: Haiku at low effort);
   session-tier for ordinary judgment work; deep-tier (Claude default:
   Opus 4.8) for heavy judgment above the session default — final
   review of a large diff, subtle-bug hunts, architecture critique;
   frontier-tier (Claude default: Fable) ONLY for work that truly needs
   the strongest model — novel architecture decisions, security-critical
   review, or a retry after a deep-tier attempt failed. State the
   dispatch rule: skills that spawn agents — at their actual spawn
   points: drain's tournament workers and per-candidate verifier runs,
   /design's candidate investigators, an on-demand verifier
   escalation — consult `.claude/runtime.md` tier pins and pass the
   mapped model through the harness's model parameter; no config, or no
   pin for the tier, → inherit the session model (the deep tiers are
   opt-in per R5 — profile rows are recommended pin values, not active
   defaults). Pins bind Agent-tool dispatch only; the headless fallback
   templates run their profile's default in v1. Do NOT restate drain's
   ranking mechanics — ranking is mechanical and spawns nothing
   (drain/reference.md "Rank"); the tier rule names spawn points only.
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

- [ ] `grep -q "scout-tier" .claude/agents/scout.md && grep -q "model: haiku" .claude/agents/scout.md && grep -qi "absent in plugin installs" .claude/agents/scout.md` → exit 0 (R2)
- [ ] `grep -q "scout-tier" .claude/rules/token-discipline.md && grep -q "scout-tier" README.md` → exit 0 (R3)
- [ ] `grep -q "tier pin" .claude/rules/token-discipline.md && grep -q "frontier-tier" .claude/rules/token-discipline.md && grep -q "deep-tier" .claude/rules/token-discipline.md` → exit 0 (R11 — routing ladder in the always-on rule)
- [ ] `grep -qi "built-in transcript evaluator" .claude/skills/autopilot/reference.md && grep -qi "built-in transcript evaluator" .claude/skills/gate/reference.md && ! grep -qi "scout-tier" .claude/skills/autopilot/reference.md && ! grep -qi "scout-tier" .claude/skills/gate/reference.md` → exit 0 (R3 — evaluator lines reworded, no tier mislabel)
- [ ] `grep -q "active runtime profile" .claude/skills/drain/reference.md && grep -q "active runtime profile" .claude/skills/autopilot/reference.md && grep -q "claude -p" .claude/skills/drain/reference.md` → exit 0 (R4)
- [ ] `grep -q "absent in plugin installs" .claude/skills/drain/reference.md && grep -q "absent in plugin installs" .claude/skills/autopilot/reference.md` → exit 0 (R5 fallback clauses in the plugin-shipped citers)
- [ ] `grep -qi "Other runtimes" README.md && grep -q "runtimes/" CLAUDE.md` → exit 0 (R9)
