# Task 01: Runtime profiles and porting guide (new files only)

Status: pending
Depends on: none
Budget: 25 turns
Spec: ../SPEC.md (requirements R1, R5 (runtimes/README.md), R7)

## Goal

Create the runtime-profile layer as new files: three profiles under
`runtimes/` mapping the abstract tiers (scout-tier, session-tier) and
headless command templates onto concrete runtimes, a `runtimes/README.md`
that is the single home of the `.claude/runtime.md` selection convention,
and `docs/porting.md` mapping toolkit concepts onto other runtimes. No
existing file is touched; the claude-code profile must reproduce today's
exact behavior.

## Touch

- runtimes/claude-code.md (new)
- runtimes/antigravity.md (new)
- runtimes/gemini-cli.md (new)
- runtimes/README.md (new)
- docs/porting.md (new)

## Steps

1. Write `runtimes/claude-code.md` with exactly three sections: `## Tiers`
   (scout-tier → Haiku + effort low; session-tier → inherit), `## Headless`
   (today's `claude -p` template with placeholders for prompt, allowlist,
   and turn cap — copy the existing contract from
   `.claude/skills/drain/reference.md` without changing it), `## Notes`
   (config file locations, permission-mode equivalents).
2. Write `runtimes/antigravity.md`: `## Tiers` (scout-tier → Flash-class;
   session-tier → session model, matching the existing `antigravity/`
   port's vocabulary), `## Headless` (states none exists — Agent Manager
   launches instead), `## Notes`.
3. Write `runtimes/gemini-cli.md`: `## Tiers` (its flash / pro
   equivalents), `## Headless` (non-interactive template with the same
   placeholders), `## Notes` including one line recording how the command
   syntax was verified, or that it requires verification before first use.
4. Write `runtimes/README.md` documenting runtime selection: a consuming
   repo creates `.claude/runtime.md` whose first non-comment line is
   `runtime: <profile-name>`; absent file means `claude-code`. This file
   is the only place the convention is stated (drain/autopilot references
   cite it in task 02, they do not restate it).
5. Write `docs/porting.md`: a concept-mapping table (skills, agents,
   rules, hooks, headless, permission modes) with columns Claude Code /
   Antigravity (citing the existing `antigravity/` port) / gemini-cli
   (citing its extension/GEMINI.md equivalents), plus a short "to add a
   runtime" checklist: write `runtimes/<name>.md`, port or map each
   concept, run `evals/runner-selftest.sh` (shipped by task 03) with the
   runtime's CLI in `RUNNER_CMD`.
6. Do NOT bump `.claude-plugin/plugin.json` — the single batch version
   bump (R10) is owned by global task 99 in specs/review-fixes.

## Acceptance

- [ ] `test -f runtimes/claude-code.md && test -f runtimes/antigravity.md && test -f runtimes/gemini-cli.md && for f in runtimes/claude-code.md runtimes/antigravity.md runtimes/gemini-cli.md; do grep -q "^## Tiers" $f && grep -q "^## Headless" $f && grep -q "^## Notes" $f || exit 1; done` → exit 0 (R1)
- [ ] `test -f runtimes/README.md && grep -q "runtime:" runtimes/README.md && grep -q ".claude/runtime.md" runtimes/README.md` → exit 0 (R5)
- [ ] `test -f docs/porting.md && grep -qi "gemini" docs/porting.md && grep -qi "antigravity" docs/porting.md && grep -q "runner-selftest" docs/porting.md` → exit 0 (R7)
