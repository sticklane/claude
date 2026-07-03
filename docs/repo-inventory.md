# Repo inventory (authoritative for the quality-gates rollout)

Generated 2026-07-02 via `find ~ -maxdepth 3 -name .git \( -type d -o -type f \)`
(excluding Library, node_modules, .venv, .Trash), classified by last-activity rule.
Paths are relative to `/Users/sjaconette`. **Quote all repo paths in scripts**
(`goal tracker` contains a space).

**Activity rule (set by Steven):** a repo is DEAD — excluded from the rollout — if it has
no commit on or after **2026-03-02** (4 months before rollout) and no source-file
modifications since that date. Dead repos get nothing: no hooks, no remediation, no
CLAUDE.md edits.

## In scope: 15 active repos

| Repo | Last commit | Existing `.git/hooks/pre-commit` | CLAUDE.md |
|---|---|---|---|
| agentic-toolkit | 2026-07-02 | none | yes |
| agentprof | 2026-07-02 (Go: `go.mod`, root `*_test.go`, Makefile with `test`/`vet` — full tier per SPEC R2's Go branch) | none | no |
| automation | none (untracked WIP; source files modified after 2026-03-02) | bd flush | no |
| dev-agents | 2026-03-15 | none | yes |
| dnd/dnd-spellbook-manager | 2026-03-18 | Claude review + bd; also `pre-commit-review`, `review-audit` | yes |
| fooszone | 2026-07-02 | bd flush chained to `pre-commit.old` — **NB: `pre-commit.old` is not a backup; it is the live first link, running staged eslint + targeted Playwright e2e** (superseded per SPEC R7a(4); e2e-at-commit retired by decision); also `pre-commit-review`, `pre-push` | yes |
| gemini-beads-cluster | 2026-03-18 | bd flush + review chain; `pre-commit.backup` occupied; `review-audit` | yes |
| hub | 2026-07-02 | none | yes |
| interview-prep | 2026-07-02 | none | yes |
| portfolio-tracker | 2026-04-05 | bd flush + review chain; `pre-commit.backup` occupied; `review-audit` | yes |
| tasks-app | 2026-03-05 | bd flush + review chain; `pre-commit-review`, `review-audit` | yes |
| tdd-git-hooks | 2026-03-18 | none | yes |
| redacted-monitor | 2026-07-02 | none | no |
| ynab-app | 2026-03-23 | Claude review; `pre-commit.old` occupied | no |
| ynab-mcp-new | 2026-03-04 | bd flush + whole-project `npx tsc --noEmit` + full `npx vitest --run` + review chain (`scripts/git-hooks/pre-commit-review`). **Tests/typecheck-at-commit are superseded by the gate design** (same recorded decision as fooszone's e2e: heavy checks move to the Stop hook via `scripts/check.sh`); R7b does not fire here (`prepare` is `npm run build`; no `scripts/git-hooks/pre-commit`) | yes |

8 of 15 had live pre-commit hooks when this inventory was generated (2026-07-02) —
mostly beads (`bd`) JSONL-flush hooks, several chaining into Claude-review steps.

> **Amendment 2026-07-03:** the bd-flush-preservation instruction that used to live
> here is **void** — beads is fully decommissioned before this rollout
> (`~/specs/work-tracking-consolidation/` done; `~/specs/beads-full-exit/` covers the
> last two repos). Existing hooks are still archived-not-clobbered per SPEC R7a, but
> NO bd behavior is carried into installed hooks (SPEC R9); the hook column above is
> historical — the installer trusts the filesystem at run time. Legacy AI-review
> steps remain intentionally retired per the deterministic-gates decision.
>
> **Amendment 2026-07-03 (scope):** `cstop` (Go: `go.mod`, Makefile, testdata;
> first commits 2026-07-03, so it postdates this table) is **added as the 16th
> active repo** — full tier per SPEC R2's Go branch; no CLAUDE.md yet (R20 gives it
> one). Wherever this inventory or the SPEC says "15 active repos", read 16.

| Repo | Last commit | Existing `.git/hooks/pre-commit` | CLAUDE.md |
|---|---|---|---|
| cstop | 2026-07-03 (Go: `go.mod`, Makefile — full tier per SPEC R2's Go branch) | none | no |

## Excluded: dead repos (21), last commit before 2026-03-02

agent-swarm-project (2025-12-07) · agent-swarm-test (2025-12-02) · claude_test (2025-03-09)
· codewalk (2026-02-04) · deploy_app (2025-03-10) · Desktop/clothing (2025-11-13) ·
fextralife-mcp (2026-03-01) · foosball-monte-carlo (2026-02-02) · foosball_video_app
(2025-11-10) · fun-browser-game (2025-12-01) · gemini-agent-swarm (2025-12-07) ·
goal tracker (2025-11-25) · mcp_agent_mail (2025-11-30) · portfolio-app (no commits, no
source activity since 2026-03-02) · project-setup (2025-12-02) · quantity-dust-mcp
(2026-02-27) · resume-and-jobhunt (2025-12-03) · sizing-app/sizing-app (2025-11-28) ·
task-tracking-app (2025-11-09) · terminal-tasks (2025-12-12) · tmux-session-monitor
(2025-12-13)

## Excluded: non-candidate `.git` entries (11)

| Path | Reason |
|---|---|
| .mcp_agent_mail_git_mailbox_repo | Hidden, machine-managed; a gating hook would reject automated commits |
| hub-worktrees/task-02 … task-10 (9 worktrees) | Git worktrees of `hub` (`.git` is a file; hooks are shared with the main checkout) |
| vaults/life | Obsidian vault, not a codebase |

## Installer exclusion rules (enforced by rule, not just by list)

Skip any target where:
1. `.git` is a **file** (git worktree — hooks live in the parent repo), or
2. any path component starts with `.` (hidden/machine-managed repos), or
3. the repo is on the **dead list above** (list membership, not a re-derived date check —
   the activity rule is how the list was built; `automation` has zero commits yet is in
   scope), or
4. the path is on the non-candidate list above.

Every excluded target must still appear in the rollout report under "excluded, reason".
