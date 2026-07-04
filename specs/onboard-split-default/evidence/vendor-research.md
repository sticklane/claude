# Official Vendor Guidance: Structuring Repos for AI Coding Agents
(researched 2026-07-03 from official Anthropic / OpenAI / Google / GitHub docs)

## Per-vendor findings

### Anthropic (Claude Code)
Sources: https://code.claude.com/docs/en/best-practices, https://code.claude.com/docs/en/memory, https://code.claude.com/docs/en/large-codebases

- CLAUDE.md include: bash commands Claude can't guess; style rules that differ from defaults; testing instructions; repo etiquette (branch/PR conventions); architectural decisions; env quirks; gotchas.
- CLAUDE.md exclude: anything inferable from code; standard language conventions; API-doc dumps; frequently-changing info; tutorials; file-by-file descriptions; platitudes. Per-line test: "Would removing this cause Claude to make mistakes?"
- Length: under 200 lines per CLAUDE.md; bloat reduces adherence. Deterministic requirements belong in hooks, not memory lines.
- Hierarchy: managed policy → ~/.claude/CLAUDE.md → ./CLAUDE.md (committed) → CLAUDE.local.md (gitignored). Subdirectory CLAUDE.md loads on demand. @path imports (depth 4). .claude/rules/*.md with paths: glob frontmatter = path-scoped rules.
- Monorepo: root CLAUDE.md = repo-wide rules + short repo map; per-package CLAUDE.md with that area's commands/conventions; per-directory skills; Read() deny rules for dist/build/generated/vendored.
- CLAUDE.md vs AGENTS.md: Claude reads CLAUDE.md only; official bridge for dual-tool repos = CLAUDE.md containing `@AGENTS.md` (or symlink). /init ingests existing AGENTS.md.
- Other: check CLAUDE.md into git; move sometimes-relevant knowledge to skills; permission allowlists for safe commands; give the agent a runnable check; revisit rules after major model releases.

### OpenAI (Codex / AGENTS.md)
Sources: https://agents.md/, https://developers.openai.com/codex/guides/agents-md, https://developers.openai.com/codex/cloud/environments

- README is for humans (quick start, pitch, contribution); AGENTS.md carries build steps, tests, conventions. Plain Markdown, no schema. Suggested sections: setup commands; build/test; code style; testing; PR/commit guidelines; security; dev-env tips incl. monorepo navigation.
- Root AGENTS.md + nested per-subpackage; closest file to the edited file wins; chat prompts override.
- Codex: root-to-cwd concatenation, closer files take precedence; one file per directory; 32 KiB default cap — hitting it means split into nested files.
- Listed lint/test commands are an executable contract: the agent runs them and fixes failures before finishing.
- Cloud env: setup + maintenance scripts; exports don't persist (use ~/.bashrc); secrets stripped before agent phase.

### Google (Gemini CLI / Jules)
Sources: https://google-gemini.github.io/gemini-cli/docs/cli/gemini-md.html, https://jules.google/docs/, https://jules.google/docs/environment/

- GEMINI.md hierarchical: ~/.gemini/GEMINI.md global; project files cwd→.git root; subdirectory files (respecting .gitignore/.geminiignore). All concatenated into every prompt. @file.md imports. context.fileName may be set to ["AGENTS.md","CONTEXT.md","GEMINI.md"] — Gemini officially supports AGENTS.md.
- Jules reads AGENTS.md from repo root; uses AGENTS.md or README.md as env-setup hints; "Keep AGENTS.md up to date."

### GitHub (Copilot coding agent)
Sources: https://docs.github.com/en/copilot/tutorials/coding-agent/get-the-best-results, https://docs.github.com/en/copilot/how-tos/configure-custom-instructions/add-repository-instructions

- Reads: .github/copilot-instructions.md; .github/instructions/**/*.instructions.md with applyTo globs; AGENTS.md anywhere (nearest wins); a single root CLAUDE.md or GEMINI.md.
- Content: high-level repo summary (size, languages, frameworks); validated build/bootstrap/test/run/lint commands; directory map with purposes; coding standards; reproducible validation steps.
- Length: "no longer than 2 pages"; must not be task-specific.
- copilot-setup-steps.yml pre-installs deps so the agent can build/test immediately. Task hygiene: scoped issues, acceptance criteria, file pointers.

### Cross-vendor convergence
AGENTS.md is the de facto cross-vendor standard (Codex, Jules, Gemini CLI, Copilot, Cursor read it natively); Anthropic is the holdout but documents the @AGENTS.md import/symlink bridge. Nested-file/closest-wins appears in all four vendors' docs.

## Consolidated checklist (by consensus strength)

Unanimous (4/4):
1. One context file at repo root with VERIFIED build/test/lint/run commands — agents execute them as their verification loop.
2. Document project layout: short directory map with purposes, not file-by-file narration.
3. Keep it short and non-task-specific (Anthropic <200 lines; GitHub ≤2 pages; Codex 32 KiB cap).
4. Nested context files per package in monorepos; root = repo-wide rules + orientation map.
5. Give the agent a runnable pass/fail check (tests/lint/build).

Strong (3/4):
6. Code style only where it differs from defaults + repo etiquette (branch naming, commit/PR format).
7. Exclude what the agent can infer from code.
8. Bridge tools, don't duplicate: @AGENTS.md import/symlink into CLAUDE.md; Gemini context.fileName; Copilot reads all.
9. Version context files, review in PRs, prune when the agent misbehaves.

Two vendors / high value:
10. Path-scoped rules (.claude/rules/ paths: globs ≙ .github/instructions applyTo globs) instead of one giant file.
11. Move sometimes-relevant procedures into on-demand mechanisms (skills) — always-loaded context is for every-session facts.
12. Scripted environment setup so a fresh agent can build immediately.
13. Keep generated/vendored/build output out of agent reach (Read-deny rules, ignore files).
14. Permission allowlists for known-safe commands so unattended runs don't stall.
15. README for humans; agent file for the mechanical contract.

Divergences: file naming (mitigated by bridges); merge semantics (Claude/Gemini concatenate, Codex/Copilot nearest-wins); only Anthropic publishes a line-count target + pruning test; only GitHub/OpenAI have declarative CI-style env setup files.

## Local audit (2026-07-03, 38 repos from ~/REPOS.md)

| Signal | Have it | Missing |
|---|---|---|
| README.md | 27 | codewalk, cstop, dev-agents, automation, portfolio-app, quantity-dust-mcp, resume-and-jobhunt, fun-browser-game, sizing-app, specs, fextralife-mcp |
| CLAUDE.md | 24 | agent-swarm-test, claude_test, deploy_app, foosball_video_app, goal tracker, mcp_agent_mail, project-setup, sizing-app, specs, task-tracking-app, tmux-session-monitor, fextralife-mcp, .mcp_agent_mail_git_mailbox_repo |
| AGENTS.md | 10 | all others (no bridge convention exists yet) |
| docs/TASKS.md | 13 | — |
| scripts/check.sh | 10 | — |

Repos with NONE of the signals: sizing-app, specs, fextralife-mcp, .mcp_agent_mail_git_mailbox_repo.
