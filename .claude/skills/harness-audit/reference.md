# harness-audit reference

Per-area check detail for the five checklist areas in
[SKILL.md](SKILL.md). The SKILL.md body names the shape of each check; this
file holds the concrete commands a scout runs. All commands here are
read-only inspection unless the SKILL.md's mutation-class scoping (area 1)
explicitly clears one for execution.

## Table of Contents

- [1. Command currency](#1-command-currency)
- [2. Gate coverage](#2-gate-coverage)
- [3. Evalset presence](#3-evalset-presence)
- [4. Memory hygiene](#4-memory-hygiene)
- [5. Allowlist drift](#5-allowlist-drift)

## 1. Command currency

Enumerate documented commands, then classify each before running:

- Collect candidates from `AGENTS.md`'s `## Commands` section, CLAUDE.md's
  Checks/Commands prose, and build files (`package.json` scripts,
  `Makefile`, `justfile`, `scripts/*.sh`).
- Read the repo's allowlist (`.claude/settings.json` /
  `.claude/settings.local.json` `permissions.allow`).
- **Mutation class**: treat build / deploy / migrate / publish / commit /
  push / release verbs (and anything with side effects on disk, network, or
  a database) as mutating. When in doubt, classify as mutating — inspect,
  don't execute.
- **Execute** iff read-only AND allowlisted: run it, capture the exit code.
  Nonzero (and not a documented expected failure) → finding.
- **Inspect only** otherwise: confirm the referenced script/target file
  exists (`test -e`) and resolves; a dangling reference → finding.

Finding shape: `<file>: command "<cmd>" <stale reason> — fix: <one line>`.

## 2. Gate coverage

- Detect gates: `.claude/settings.json` with a `Stop` hook entry, and a git
  pre-commit hook (`.git/hooks/pre-commit`) or the repo's VCS equivalent.
- If absent → single line `gate coverage: no gates installed` (not a
  per-file finding).
- If present → read the check entrypoint the hooks invoke (commonly
  `scripts/check.sh`) and confirm every command it references exists. Run
  the check on a clean tree (`git status` clean first) and confirm exit 0.
  A missing referenced check, or a nonzero exit on a clean tree, is a
  finding.

## 3. Evalset presence

- List skills: `.claude/skills/*/SKILL.md`.
- For each, check whether an evalset exists (repo convention: e.g. an
  `evals/` entry or a stored evalset the runner recognizes) and compare the
  skill file's last-changed revision against the last recorded eval run.
- Findings: skills changed since their last eval run, and skills with no
  evalset at all. None → `evalset presence: clean`.

## 4. Memory hygiene

- Parse `docs/memory.md` index entries (the linked `docs/memory/*.md`
  paths).
- Forward check: every indexed path resolves to an existing file
  (`test -e`).
- Reverse check: every file in `docs/memory/` appears in the index.
- Flag stale-dated entries (a date field older than the repo's staleness
  threshold, or a dead reference to a since-renamed spec).
- Findings name the specific entry/file and the fix (add index line, remove
  orphan, refresh date). Consistent → `memory hygiene: clean`.

## 5. Allowlist drift

- Read `permissions.allow` from settings.
- Cross-reference recent transcripts (the harness's transcript store) for
  which allowlisted patterns were actually exercised.
- Findings: (a) entries granted but unused in recent transcripts — candidate
  for removal; (b) prompt patterns that recur without a matching entry —
  candidate for adding. None → `allowlist drift: clean`.

Transcript access is read-only; if transcripts are unavailable in the
current context, emit `allowlist drift: transcripts unavailable — skipped`
rather than silently dropping the area (the silent-skip failure mode R2
guards against).
