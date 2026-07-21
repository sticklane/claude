---
name: harness-audit
description: Audits an already-onboarded repo's harness health against a fixed checklist and emits a ranked findings report - command currency, gate coverage, evalset presence, memory hygiene, and allowlist drift - read-only, never auto-fixing. Use when the user says "audit this repo's harness", "check the harness", "harness health check", "is the harness drifted", or "audit the harness".
argument-hint: "[repo path to audit, defaults to cwd]"
---

**Read-only contract (read first; the rest of the body may truncate on
compaction but this must not).** harness-audit makes NO edits, installs
nothing, and never auto-fixes. It only reads files, executes commands that
are BOTH read-only AND permitted by the repo's execution policy (the
Terminal Execution Policy allowlist), and inspects (never executes) mutating
commands. Every finding's next step is a normal task/spec filed through the
pipeline — never an in-audit edit. `git status` must be clean when the audit
finishes; if it is not, the audit has a bug. This contract is R1 of
specs/harness-audit/SPEC.md.

Audit the repo at $ARGUMENTS (default: cwd) against the five-area checklist
below. Each area MUST produce either concrete findings or an explicit
"clean" line — a silent skip is the exact failure mode this skill exists to
catch (R2). Detailed per-area check commands live in
[reference.md](reference.md), loaded on demand.

## Procedure

Areas 1–5 are mechanical (command runs, file-existence greps, index
cross-checks). Dispatch each as a scout-tier conversation (the scout skill)
per the dispatch-tier rule below; only the final ranking/synthesis step
(area 6) runs on the session model.

### 1. Command currency

Scope every documented command (from `AGENTS.md`'s `## Commands` section and
build files) by mutation class BEFORE running anything:

- **Execute** a command only if it is BOTH read-only AND permitted by the
  repo's execution-policy allowlist. Allowlist membership alone is NOT
  sufficient — an execution policy can permit mutating commands (e.g. a
  `git commit` allow), and executing one would break R1's read-only
  contract. An executed command must exit 0 (or match a documented expected
  failure); a nonzero exit is a finding.
- **Inspect only** — never execute — any command that mutates (build, deploy,
  migrate, publish, and similar), regardless of allowlist membership. Confirm
  the command still exists and the file/target it references is still valid;
  a missing script or dangling target is a finding.

Emit findings for stale/broken commands, or one "command currency: clean"
line.

### 2. Gate coverage

If gates are installed (`.agents/hooks.json` PostToolUse/PreToolUse hooks,
plus the git pre-commit layer), confirm the checks they reference still
exist and pass on a clean tree. A referenced check that no longer exists, or
fails on a clean tree, is a finding. Antigravity has no per-turn Stop gate
(its Stop event fires at session end), so the CI backstop that runs the same
checks on push is part of gate coverage — confirm it references live checks
too. If gates are NOT installed, say so ONCE ("gate coverage: no gates
installed") — not as a finding per file.

### 3. Evalset presence

For toolkit-style repos, read the tier policy in `evals/COVERAGE.md` (cite it;
don't restate the table) and judge each skill against its row rather than
flagging every evalset-less skill equally:

- **Tier A** — a skill under its scenario bar (or with no evalset), or one
  changed since its last eval run, is a finding.
- **Tier B** — check the row's named model-free test file(s) exist and are
  current; a missing named test is a finding.
- **Tier C** — report as waived in one line echoing the row's recorded
  reason, not a per-skill finding.
- A skill directory absent from `evals/COVERAGE.md` is itself the finding —
  the policy must name every skill.

No gaps → "evalset presence: clean".

### 4. Memory hygiene

Cross-check `docs/memory.md` against `docs/memory/`: every index entry must
resolve to a file, and every file must be indexed (both directions). Flag
stale-dated entries. Unresolved entries, orphaned files, and stale dates are
findings; a fully consistent index → "memory hygiene: clean".

### 5. Allowlist drift

Compare the permission/execution-policy allowlist against recent
conversation transcripts: flag entries granted but unused, and prompts that
recur without a matching entry. Each is a finding; no drift → "allowlist
drift: clean".

### 6. Rank and synthesize (session model)

Collect every area's findings and rank them blocking → advisory. Each
finding names its file and a one-line fix. State explicitly that a finding's
next step is a normal task/spec through the pipeline, NEVER an in-audit edit.
Emit the ranked list to the session; write nothing to disk.

## Dispatch tier

Areas 1–5 are mechanical checks — dispatch each as a scout-tier conversation
(read-only; the scout skill, on the scout tier of the active runtime
profile in `runtimes/`) per `.claude/rules/token-discipline.md`'s "Dispatch
authoring" section (tier by stage type, cap each return at a structured
findings summary, bound the fan-out to the five areas). Cite that section
rather than restating it. Only the ranking/synthesis step (area 6) runs on
the session model — it is the judgment stage (R4).

Next stage: none — file findings as tasks/specs per normal pipeline.
