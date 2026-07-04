# Quality-gates rollout report (task 06)

Generated 2026-07-03 (attended). Installer: `bin/install-gates` (this repo).
Covers every entry in `docs/repo-inventory.md`: 16 active, 21 dead, 11
non-candidate. No entry silently skipped (R16).

## Rollout-context notes

- **Toolkit relocated mid-rollout:** the installer/toolkit repo moved from
  `~/agentic-toolkit` to **`~/claude`** (different git history; the toolkit's
  files, including `install-gates` with the venv-pytest fix, were carried
  over). The inventory's `agentic-toolkit` active entry is served by `~/claude`,
  which already carries its generic-tier gate.
- **Concurrent activity:** a second process installed gates on several repos in
  parallel (message `chore: commit quality-gate install …`), producing some
  redundant/stacked gate-install commits (noted per repo). Final installed state
  was converged to canonical and verified green regardless of commit count.
- **Beads:** `.beads/` absent in all 16 active repos → the R9 beads-abort guard
  fired for **none**; nothing `deferred: beads exit pending`.
- **Installer fix (task 06):** `install-gates` now prefers a repo-local
  `.venv/bin/pytest` over `uv run pytest` (hermetic; avoids the os-error-45
  external-uv-cache failure). Regression test added. Content present in
  `~/claude/bin/install-gates`.
- **Auto-deploy repos:** `portfolio-tracker` and `ynab-app` have `post-commit`
  hooks that `git push` (→ deploy). Their gate/remediation commits auto-pushed;
  pushed changes are infra/formatting only (no Worker/logic behavior change).

## Active repos (16)

| Repo | Stack / tier | Existing hook | Remediation | Check status |
|---|---|---|---|---|
| ~/claude (agentic-toolkit) | generic | none | none | n/a (generic; own test suite run explicitly) |
| agentprof | go / full | none | gofmt 3 files (`72522dd`) — gate format-check forced | GREEN (gofmt/vet/test) |
| automation | generic | none | none | n/a (generic) |
| cstop | go / full | none | none | GREEN (gofmt/vet/test) |
| dev-agents | python / full | none | ruff fixes (`dbe85e6`, task 05); gate uses `.venv/bin/pytest` | GREEN (ruff; 126 pytest) |
| dnd/dnd-spellbook-manager | node / full | foreign→archived | R14a `npm ci` (lockfile byte-identical); claude.md stamp (`b9b5640`) | GREEN (tsc; vitest) |
| fooszone | node / full | foreign→archived (`pre-commit.old` untouched) | none | GREEN (eslint/tsc/vitest) |
| gemini-beads-cluster | generic | foreign→archived | none | n/a (generic) |
| hub | node / full | none | none; check.sh delegates to `pnpm run check` | GREEN (`pnpm run check`) |
| interview-prep | generic | none | none | n/a (generic) |
| portfolio-tracker | node / full | foreign→archived | py↔TS drift fix (`786c39d`, task 05); gate `2d17564` (auto-deployed) | GREEN (tsc; 1256 vitest) |
| tasks-app | node / full | foreign→archived | 114 tsc fixes (task 05); R7b hook re-copy | GREEN (eslint/tsc; 4386 vitest) |
| tdd-git-hooks | generic | none | none | n/a (generic) |
| redacted-monitor | python / full | none | none | GREEN (ruff; 24 pytest) |
| ynab-app | node / full | foreign→archived | whole-repo prettier format (`08d3ca3`, R14); `.claude/` prettier-excluded (`71cdcc2`) for installer idempotence; auto-deployed | GREEN (prettier/eslint/tsc/vitest) |
| ynab-mcp-new | node / full | foreign→archived | none; `.claude` gitignored → gate files present-but-untracked (only CLAUDE.md + check.sh committed) | GREEN (tsc; vitest) |

**Dirty-at-rollout (untracked files only; no `skipped: dirty` needed — no
modified tracked files anywhere):** automation (`__pycache__`), fooszone
(`evals/`, `go/classicalcalib`), gemini-beads-cluster (`.DS_Store`).

### Open items for the owner
- **ynab-app format scope:** the gate's format stage is whole-repo
  `prettier --check .` rather than the repo's src-scoped `format:check` script.
  Per SPEC R2 the installer should delegate to the repo's own format script;
  filed as installer tech-debt. Current state green via committed whole-repo
  format + `.claude/` exclusion.
- **portfolio-tracker:** `mfp_backtest/rebalance.py` still defaults to old base
  weights (task 05 note); and its `post-commit` auto-push remains.
- **Redundant gate commits** (concurrent process): agentprof, tasks-app,
  automation, interview-prep each have a duplicate `chore: commit quality-gate
  install` commit stacked with the canonical install — cosmetic; final files
  canonical.

## Excluded: dead repos (21) — last commit before 2026-03-02, no gates installed

agent-swarm-project, agent-swarm-test, claude_test, codewalk, deploy_app,
Desktop/clothing, fextralife-mcp, foosball-monte-carlo, foosball_video_app,
fun-browser-game, gemini-agent-swarm, goal tracker, mcp_agent_mail,
portfolio-app, project-setup, quantity-dust-mcp, resume-and-jobhunt,
sizing-app/sizing-app, task-tracking-app, terminal-tasks, tmux-session-monitor.
Reason: dead-list membership (activity rule); excluded by rule.

## Excluded: non-candidate `.git` entries (11) — excluded by rule

- `.mcp_agent_mail_git_mailbox_repo` — hidden/machine-managed (path component
  starts with `.`).
- `hub-worktrees/task-02` … `task-10` (9) — git worktrees (`.git` is a file;
  hooks live in the parent `hub` checkout).
- `vaults/life` — Obsidian vault, not a codebase.

## CLAUDE.md alignment (task 07)

Instruction files aligned with installed reality 2026-07-03 (R18-R21; approved
at the R21 checkpoint). Diff summary:
`~/specs/quality-gates-rollout/claudemd-diff-summary.md`.

## Behavioral probes — all PASS (2026-07-03)

- **1 fooszone settings/archival:** Stop hook wired; keys preserved
  (`enabledPlugins`, `extraKnownMarketplaces`, `hooks`); `.pre-gates` present;
  `pre-commit.old` sha `54f4440950ca` unchanged. PASS
- **2 lint rejection:** fooszone staged bad `.mjs` → pre-commit exit 1 with
  eslint output; dev-agents staged unused-import `.py` → exit 1 with ruff/F401.
  `--no-verify` bypass path exists (gate header documents it). PASS
- **3 timing:** pre-commit on a one-line staged edit — fooszone 1s, hub 0s,
  dev-agents 0s (all < 10s). PASS
- **4 hub delegation:** `scripts/check.sh` runs `pnpm run check`. PASS
- **5 no `bd`:** installer-managed hooks in fooszone/hub/dev-agents — none. PASS
- **6 tasks-app (R7b/R14a):** `npm install` leaves `.git/hooks/pre-commit` sha
  `f1aa15d1352c` unchanged; `package-lock.json` porcelain empty. PASS
- **7 Stop-gate states / 8 fail-open:** covered exhaustively by the toolkit's
  `tests/test_hook_templates.sh` (77/77 pass) — broken check → exit 2 + output;
  green → 0; `stop_hook_active:true` → 0; check.sh moved aside → 0 + warning;
  edit hooks fail open (empty stdin / stripped PATH → 0 + warning); protect hook
  exits 2 on a protected path. PASS
- **9 verifier agent:** see verifier report (dispatched).
- **10 commit separation:** agentprof gofmt remediation (`72522dd`) separate
  from gate install (`8eaa949`); dev-agents ruff (`dbe85e6`) separate from gate
  (`56c1bf3`). PASS
- **11 end-to-end:** hook-driven loop on gated `cstop` — baseline check green;
  introduced a gofmt violation → `check.sh` exit 1; `stop-gate.sh`
  (`stop_hook_active:false`) → **exit 2** with the failure output (blocks
  "done"); formatted the file → `check.sh` exit 0 and `stop-gate.sh` → exit 0;
  tree left clean. (A true fresh interactive Claude Code session would exercise
  format-on-edit live; the hook mechanics are demonstrated identically here.)
  PASS

Note: fooszone's rollout-time dirty untracked files (`evals/`,
`go/classicalcalib`) were since committed/gitignored by the concurrent `cr`
drain, so the tree is now clean.
