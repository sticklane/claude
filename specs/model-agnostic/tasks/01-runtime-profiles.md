# Task 01: Runtime profiles and porting guide (new files only)

Status: pending
Depends on: none
Budget: 25 turns
Spec: ../SPEC.md (requirements R1, R5 (runtimes/README.md), R7, R12)

## Goal

Create the runtime-profile layer as new files: three profiles under
`runtimes/` mapping the abstract tiers (scout-tier, session-tier,
deep-tier, frontier-tier), headless command templates, and
orchestration surfaces onto concrete runtimes, a `runtimes/README.md`
that is the single home of the
`.claude/runtime.md` selection convention and the tier-override line
format, and `docs/porting.md` mapping toolkit concepts onto other
runtimes. No existing file is touched; the claude-code profile must
reproduce today's exact behavior.

## Touch

- runtimes/claude-code.md (new)
- runtimes/antigravity.md (new)
- runtimes/gemini-cli.md (new)
- runtimes/README.md (new)
- docs/porting.md (new)

## Steps

1. Write `runtimes/claude-code.md` with exactly four sections (`## Tiers`,
   `## Headless`, `## Orchestration`, `## Notes`): `## Tiers`
   (scout-tier → Haiku + effort low; session-tier → inherit; deep-tier →
   Opus 4.8 (`claude-opus-4-8`; Agent-tool short name `opus`);
   frontier-tier → Fable (`claude-fable-5`; short name `fable`); the two
   deep-tier rows marked as recommended pin values — opt-in per R5, not
   active defaults),
   `## Headless` (today's `claude -p` template with placeholders for
   prompt, allowlist, and turn cap — copy the existing contract from
   `.claude/skills/drain/reference.md` without changing it),
   `## Orchestration` (five fields per the spec's R1: primitive = the
   Workflow tool; invocation surface = named deterministic scripts in
   `.claude/workflows/` behind the human "ultracode" opt-in (cite
   docs/human-gates.md reason 5); structured output = schema-validated
   returns; resume = journaled, cached-prefix; parallelism cap =
   per-run concurrency cap), `## Notes`
   (config file locations, permission-mode equivalents).
2. Write `runtimes/antigravity.md`: `## Tiers` (scout-tier → Flash-class;
   session-tier → session model, matching the existing `antigravity/`
   port's vocabulary; deep-tier and frontier-tier → its strongest
   available model, or an explicit "no distinct mapping — session model"
   line), `## Headless` (states none exists — Agent Manager launches
   instead), `## Orchestration` (no scripted fan-out: sequential
   markdown workflows plus human-dispatched Agent Manager parallelism —
   orchestrations degrade to a human launch list), `## Notes`.
3. Write `runtimes/gemini-cli.md`: `## Tiers` (its flash / pro
   equivalents; same deep-tier/frontier-tier rule as step 2), `## Headless`
   (non-interactive template with the same placeholders),
   `## Orchestration` (none native — shell fan-out around headless
   calls with JSON output), `## Notes`
   including one line recording how the command syntax was verified, or
   that it requires verification before first use.
4. Write `runtimes/README.md` documenting runtime selection: a consuming
   repo creates `.claude/runtime.md` whose first non-comment line is
   `runtime: <profile-name>`; absent file means `claude-code`. This file
   is the only place the convention is stated (drain/autopilot references
   cite it in task 02, they do not restate it). Per R12, it also
   documents the four-rung ladder and the tier-override line format
   (`<tier-name>: <model>` — an unlisted scout/session tier keeps the
   profile default; the deep tiers are opt-in, their profile rows being
   recommended pin values, not active defaults) with one worked example
   block pinning `deep-tier: claude-opus-4-8` and `frontier-tier:
   claude-fable-5`, presented as exactly how a repo turns the Claude
   deep-work defaults ON, and states that tier pins bind dispatchers
   (skills that spawn agents via the harness), not the interactive
   session's own model and not the headless fallback path in v1.
5. Write `docs/porting.md`: a concept-mapping table (skills, agents,
   rules, hooks, headless, orchestration — workflows/fan-out — and
   permission modes) with columns Claude Code /
   Antigravity (citing the existing `antigravity/` port) / gemini-cli
   (citing its extension/GEMINI.md equivalents), plus a short "to add a
   runtime" checklist: write `runtimes/<name>.md`, port or map each
   concept, run `evals/runner-selftest.sh` (shipped by task 03) with the
   runtime's CLI in `RUNNER_CMD`.
6. Do NOT bump `.claude-plugin/plugin.json` — the single batch version
   bump (R10) is owned by global task 99 in specs/review-fixes.

## Acceptance

- [ ] `test -f runtimes/claude-code.md && test -f runtimes/antigravity.md && test -f runtimes/gemini-cli.md && for f in runtimes/claude-code.md runtimes/antigravity.md runtimes/gemini-cli.md; do grep -q "^## Tiers" $f && grep -q "^## Headless" $f && grep -q "^## Orchestration" $f && grep -q "^## Notes" $f || exit 1; done` → exit 0 (R1)
- [ ] `grep -q "deep-tier" runtimes/claude-code.md && grep -q "claude-opus-4-8" runtimes/claude-code.md && grep -q "claude-fable-5" runtimes/claude-code.md && for f in runtimes/antigravity.md runtimes/gemini-cli.md; do grep -q "deep-tier" $f && grep -q "frontier-tier" $f || exit 1; done` → exit 0 (R1 — all four tiers mapped in every profile)
- [ ] `test -f runtimes/README.md && grep -q "runtime:" runtimes/README.md && grep -q ".claude/runtime.md" runtimes/README.md` → exit 0 (R5)
- [ ] `grep -q "deep-tier: claude-opus-4-8" runtimes/README.md && grep -q "frontier-tier: claude-fable-5" runtimes/README.md` → exit 0 (R12 — override format with worked example)
- [ ] `test -f docs/porting.md && grep -qi "gemini" docs/porting.md && grep -qi "antigravity" docs/porting.md && grep -q "runner-selftest" docs/porting.md` → exit 0 (R7)
