# Verification evidence: task 02 (onboard + record + mirror)

Verdict: PASS
Verified: 2026-07-03, branch task/02-onboard-and-record, HEAD 790b418
Verifier: independent (did not write this code)

## Acceptance commands (run from repo root)

### R4 — onboard encodes the practices

```
grep -qi "repo map" .claude/skills/onboard/SKILL.md \
  && grep -q "per-directory CLAUDE.md" .claude/skills/onboard/SKILL.md \
  && grep -q "AGENTS.md" .claude/skills/onboard/SKILL.md \
  && grep -qi "open work" .claude/skills/onboard/SKILL.md
```
Exit code: 0 — PASS

Substantive check (all four additions sit in the skill's existing
structure, per R4):
- "A short repo map: one pointer line per top-level area…" — new bullet
  inside section 3's Include list; says "the file-by-file exclusion below
  still applies to the map" (extends, does not restate, the exclusion).
- "Where open work lives, if the repo uses the spec pipeline: specs/,
  task `Status:` headers, and the status script if present." — second
  new Include bullet.
- "Monorepos and large repos: subsystem detail belongs in per-directory
  CLAUDE.md files, which load on demand… the root map stays small." —
  note appended to section 3 after the Exclude paragraph.
- Root `AGENTS.md` interop offer — first item in section 5 "Offer the
  next layer": pointer-only, "mirroring nothing that would drift";
  names Codex/Jules/Kiro native, gemini-cli via `context.fileName`,
  Claude Code via `@AGENTS.md` import. Matches R4's content.

### R5 — research record

```
sed -n '/[Rr]epo orientation for agents/,/^## /p' docs/external-playbooks.md | grep -qi "agents.md" \
  && sed -n '/[Rr]epo orientation for agents/,/^## /p' docs/external-playbooks.md | grep -qi "kiro" \
  && sed -n '/[Rr]epo orientation for agents/,/^## /p' docs/external-playbooks.md | grep -qi "llms.txt"
```
Exit code: 0 — PASS

Substantive check — `## Repo orientation for agents` section (appended,
lines 231-267) contains, with source URLs:
- Convergence: small always-on root file — Anthropic <200 lines
  (code.claude.com/docs/en/memory), Codex 32 KiB `project_doc_max_bytes`
  (developers.openai.com/codex/guides/agents-md).
- Convergence: pointers/JIT — "file-by-file descriptions" exclusion,
  "lightweight identifiers" (anthropic.com/engineering/effective-context-engineering-for-ai-agents).
- Convergence: nearest-file-wins hierarchy — agents.md, gemini-cli
  GEMINI.md, code.claude.com/docs/en/large-codebases.
- Convergence: structured work-state — Kiro specs
  (kiro.dev/docs/specs) and steering (kiro.dev/docs/steering).
- Convergence: AGENTS.md interop standard — Linux Foundation; native in
  Codex/Jules/Kiro CLI/Android Studio; gemini-cli via
  `context.fileName`; Claude Code via import or symlink.
- Divergences: Kiro always/fileMatch/manual vs Claude Code `paths:`;
  AGENTS.md not honored by gemini-cli by default.
- llms.txt line: "no coding tool consumes a repo's llms.txt — skipped
  here."
All R5 items present.

### R6 — antigravity mirror

```
grep -qi "repo map" antigravity/.agents/skills/onboard/SKILL.md \
  && grep -q "per-directory" antigravity/.agents/skills/onboard/SKILL.md
```
Exit code: 0 — PASS

Substantive check: mirror carries the repo-map and work-state Include
bullets verbatim; the monorepo note is adapted to Antigravity's native
file ("per-directory (nested) AGENTS.md files, read nearest-file-wins");
the AGENTS.md interop offer is NOT added to section 5 (offers list has
only /gate and artifact-review, unchanged) and is replaced by the
required one-sentence note: "No separate interop file is needed:
AGENTS.md is already the cross-tool standard and Antigravity's native
context file." Matches R6.

## plugin.json (R7 owned by review-fixes 99)

`git diff main -- .claude-plugin/plugin.json` — empty; version remains
"0.6.2". Confirmed NOT bumped, as the task requires.

## Scope check

`git diff main --name-only`:
```
.claude/skills/onboard/SKILL.md
antigravity/.agents/skills/onboard/SKILL.md
docs/external-playbooks.md
```
Exactly the task's Touch list; `git status --porcelain` shows no
untracked files. No scope creep.

## Gates

- No project build/lint/test suite applies to these markdown-only edits.
- /evals gate: no stored evalset for onboard (`evals/` contains only
  `breakdown`), so the "run /evals before committing any skill change"
  gate does not apply.
- SKILL.md conventions spot-check: onboard body remains well under 500
  lines; changes slot into existing numbered sections.

## Findings

None blocking. Note: changes are uncommitted in the working tree
(expected at verify time; drain owns the merge/commit).
