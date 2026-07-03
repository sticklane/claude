# Verification: task 01-runtime-profiles

Verdict: PASS
Verified: 2026-07-03, branch task/01-runtime-profiles (uncommitted working tree)
Verifier: independent (did not write this code)

## Acceptance commands (all run from repo root)

1. ✓ AC1 (R1 — three profiles, four sections each)
   `test -f runtimes/claude-code.md && test -f runtimes/antigravity.md && test -f runtimes/gemini-cli.md && for f in runtimes/claude-code.md runtimes/antigravity.md runtimes/gemini-cli.md; do grep -q "^## Tiers" $f && grep -q "^## Headless" $f && grep -q "^## Orchestration" $f && grep -q "^## Notes" $f || exit 1; done`
   → exit 0

2. ✓ AC2 (R1 — all four tiers mapped in every profile)
   `grep -q "deep-tier" runtimes/claude-code.md && grep -q "claude-opus-4-8" runtimes/claude-code.md && grep -q "claude-fable-5" runtimes/claude-code.md && for f in runtimes/antigravity.md runtimes/gemini-cli.md; do grep -q "deep-tier" $f && grep -q "frontier-tier" $f || exit 1; done`
   → exit 0

3. ✓ AC3 (R5)
   `test -f runtimes/README.md && grep -q "runtime:" runtimes/README.md && grep -q ".claude/runtime.md" runtimes/README.md`
   → exit 0

4. ✓ AC4 (R12 — override format with worked example)
   `grep -q "deep-tier: claude-opus-4-8" runtimes/README.md && grep -q "frontier-tier: claude-fable-5" runtimes/README.md`
   → exit 0

5. ✓ AC5 (R7)
   `test -f docs/porting.md && grep -qi "gemini" docs/porting.md && grep -qi "antigravity" docs/porting.md && grep -q "runner-selftest" docs/porting.md`
   → exit 0

## Substantive checks against the Steps

- Exactly four sections per profile: `grep -c "^## "` → 4 for all three
  files; headings are Tiers | Headless | Orchestration | Notes in order.
- claude-code.md Tiers: scout-tier = Haiku + effort low; session-tier =
  inherit; deep-tier = Opus 4.8 (`claude-opus-4-8`, short name `opus`);
  frontier-tier = Fable (`claude-fable-5`, short name `fable`). Both
  deep rows carry "Recommended pin value — opt-in, not an active
  default" in the table AND a paragraph restating opt-in semantics.
- claude-code.md Headless matches the contract in
  `.claude/skills/drain/reference.md` (lines 173–195): `claude -p
  "<prompt>" --allowedTools "<allowlist>" --permission-mode dontAsk
  --max-turns <cap>`; allowlist example identical
  (`Read,Edit,Write,Glob,Grep,Bash(...),Bash(git add *),Bash(git commit *)`);
  turn cap = task Budget else 80; drain reference itself NOT modified
  (git status clean for `.claude/`).
- claude-code.md Orchestration records all five fields: primitive =
  Workflow tool; invocation surface = `.claude/workflows/` scripts
  behind human "ultracode" opt-in, citing docs/human-gates.md reason 5
  (verified: reason 5 in that file names the "ultracode" keyword);
  structured output = schema-validated returns; resume = journaled,
  cached-prefix; parallelism cap = per-run concurrency cap.
- antigravity.md: Headless states none exists — Agent Manager launches
  instead. Orchestration: no scripted fan-out, degrades to a human
  launch list. Tiers use the port's vocabulary ("Flash-class model for
  scouting" — confirmed verbatim in antigravity/README.md line 48);
  deep/frontier = strongest model in picker, marked recommended pin /
  opt-in. All five orchestration fields present.
- gemini-cli.md: flash/pro tier mapping with deep tiers marked
  recommended pin / opt-in; headless template with prompt / allowlist /
  turn-cap placeholders; orchestration = none native, shell fan-out
  with `-o json`, five fields present. Notes records verification:
  "verified against the `gemini --help` output of gemini-cli v0.46.0
  (Homebrew, 2026-07-03)". Independently substantiated: gemini 0.46.0
  is installed via Homebrew on this machine, and `gemini --help`
  confirms `-p/--prompt` (headless), `--approval-mode
  default/auto_edit/yolo/plan`, `--allowed-tools` marked DEPRECATED in
  favor of the Policy Engine, `--policy`, `-r/--resume`,
  `--session-file`, `-o/--output-format json|stream-json` — all
  matching the profile's claims.

## runtimes/README.md (R5 + R12)

- Selection convention: `.claude/runtime.md`, first non-comment line
  `runtime: <profile-name>`, absent file = `claude-code` (lines 17–29).
- Declares itself the single home ("This file is the single home of the
  selection convention and the tier-override format", lines 13–15).
  Repo-wide grep: `.claude/runtime.md` appears only in
  runtimes/README.md and as a citation (not restatement) in
  runtimes/claude-code.md and (README link) antigravity.md /
  gemini-cli.md. Drain/autopilot citations are task 02's scope.
- Four-rung ladder documented (lines 31–43).
- Override format `<tier-name>: <model>`; unlisted scout/session tier
  keeps profile default; deep tiers opt-in, profile rows = recommended
  pin values (lines 45–60).
- Worked example block pins `deep-tier: claude-opus-4-8` and
  `frontier-tier: claude-fable-5`, introduced as "exactly how a repo
  turns the Claude deep-work defaults ON" (lines 62–69).
- States pins bind dispatchers, NOT the interactive session's own model
  and NOT the headless fallback path in v1 (lines 74–82).

## docs/porting.md (R7)

- Concept-mapping table has exactly the seven concept rows: Skills,
  Agents, Rules, Hooks, Headless, Orchestration (workflows/fan-out),
  Permission modes; three runtime columns (Claude Code / Antigravity
  citing `antigravity/` / gemini-cli citing GEMINI.md, `gemini skills`,
  `gemini hooks`).
- "To add a runtime" checklist present; step 3 names
  `evals/runner-selftest.sh` (attributed to task 03) and `RUNNER_CMD`.

## Scope / gates

- `git status --porcelain`: ` M specs/model-agnostic/tasks/01-runtime-profiles.md`
  plus untracked `docs/porting.md` and `runtimes/` (exactly the five
  Touch files; `ls runtimes` → antigravity.md claude-code.md
  gemini-cli.md README.md, nothing extra).
- `git diff` on the task file: Status `pending` → `in-progress` only.
  (Note: implementer left Status at in-progress, not done — a
  bookkeeping observation, not a failure; the criterion permits only
  the Status line to change and that holds.)
- `.claude-plugin/plugin.json` NOT modified (no diff; version 0.6.0
  unchanged), per task step 6 / R10.
- No existing file modified anywhere else; drain/autopilot references,
  scout.md, rules all untouched (those belong to task 02).
- Standard gates: repo has no package.json/Makefile/pre-commit config;
  evals/run.sh applies to skill changes only and no skill changed —
  no applicable gate.
- Overfitting check: acceptance criteria are grep-shaped; content
  behind each grep was read in full and is substantive, not
  keyword-stuffed. External claims (gemini flags, antigravity
  vocabulary, human-gates reason 5) verified against their sources.
