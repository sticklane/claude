# Shell text-tool doctrine: sed/awk/grep alignment across toolkit skills

Breakdown-ready: true

## Problem

The toolkit's skills freely embed `grep`/`sed`/`awk` in guidance and
acceptance commands (20+ files under `.claude/skills/`), but no rule
codifies WHEN shell text tools are appropriate for agents versus the
harness's dedicated tools. External best practice is consistent and
specific (2026-07-20 research):

- Agents drifting from dedicated Read/Edit/Glob/Grep tools to raw
  `sed`/`cat`/`ls` is a tracked failure mode (anthropics/claude-code
  issue #21697): dedicated tools carry safety the shell lacks —
  Edit's uniqueness validation + read-before-write requirement +
  reviewable diffs vs `sed -i`'s silent regex corruption.
- ACI research (SWE-agent; Open SWE) converges on bounded, structured
  output: no cat-the-whole-file, no unbounded `grep -rn`; every
  command's output should have a maximum size.
- Read-only extraction is the legitimate niche: `grep`/`awk`/`sed -n`
  for acceptance checks, log slicing, and pipelines — where a
  dedicated tool has no equivalent — capped with `head`/`-l`/
  `--max-count`/anchored ranges.

Today's live evidence, same session: a spec acceptance written as a
file-wide literal grep collided with an unrelated doc comment
(fooszone go-cmd-shared-helpers R3, caught by critique; fixed with a
function-anchored `awk '/^func …/,/^}/'` range) — anchored-range
extraction is a skill worth teaching, not banning. One legitimate
write-side exception exists and is already documented per-repo: a
PostToolUse .md formatter can reflow Edit/Write output, so fenced-code
.md files are sometimes better edited Bash-side (fooszone CLAUDE.md) —
an exception to record, not silently contradict. The gate skill
already pairs its Stop hook with `Bash(sed -i *)` deny-rule advice
(gate/reference.md:172-173); nothing generalizes that.

## Solution

One short rule file plus an audit-and-fix pass over skill-embedded
commands. No new tooling.

## Requirements

- R1 — Rule file `.claude/rules/shell-text-tools.md` (≤60 lines)
  stating: (a) writes to source/docs go through Edit/Write — never
  `sed -i`, in-place `awk`, `cat >`/`>>` onto tracked files, with the
  documented exceptions enumerated (formatter-reflow .md heredoc case;
  generated/derived files); (b) reads of a file you will edit use Read;
  (c) shell text tools are for read-only extraction with BOUNDED
  output — every example caps via `head`, `grep -l/-m/-c`, `sed -n`
  ranges, or `awk` anchored ranges; (d) acceptance-command authoring
  guidance: anchor greps to structure (function/section ranges, line
  starts like `^## `, frontmatter-line extraction via `sed -n
's/^description: *//p'`) rather than file-wide literals — citing the
  doc-comment collision class; (e) cross-reference gate's deny-rule
  pairing and token-discipline's delegation default. Acceptance: file
  exists; each of (a)-(e) present; `wc -l` ≤ 60.
- R2 — Skill audit: sweep `.claude/skills/**/SKILL.md` and
  `reference.md` for embedded `sed`/`awk`/`grep`/`cat` commands; every
  WRITE-shaped usage (sed -i, cat > tracked file) is either removed,
  converted to Edit/Write instruction, or annotated as a documented R1
  exception; every read-shaped example is bounded per R1(c). Produce
  the sweep as a table in the task's evidence (file, line, verdict:
  ok/bounded-fix/write-violation) — silent "all fine" without the
  table fails R2. Mirror-affected files follow the mirror rules
  (.claude/rules/mirror-procedure-discipline.md).
- R3 — Authoring-skill propagation: the skills that TEACH command
  authoring (idea, breakdown, critique — wherever acceptance-criteria
  guidance lives) gain one line pointing at R1's rule so newly
  authored specs inherit the anchored-and-bounded acceptance style.
  Acceptance: `grep -l 'shell-text-tools' .claude/skills/idea/SKILL.md
.claude/skills/breakdown/SKILL.md` matches both (or the file where
  each actually carries acceptance guidance, named in the task).
- R4 — Rules-file distribution parity: if `.claude/rules/*.md` are
  mirrored (antigravity/codex trees), the new rule rides the same
  mirror procedure; verify per mirror-verification.md. If rules are
  not mirrored, record that finding in evidence and skip.

## Non-goals

- Changing harness permissions/deny lists globally (gate owns that,
  per-repo).
- Policing ad-hoc interactive use — the rule governs skill-embedded
  guidance and spec acceptance commands, the things agents copy.

## Sources

- github.com/anthropics/claude-code/issues/21697 (subagents drift to
  sed/cat/ls over dedicated tools)
- SWE-agent ACI findings + Open SWE bounded-output design
  (dev.to/truongpx396/swe-agent-deep-dive-build-your-own-guide-ade;
  langchain.com/blog/open-swe-an-open-source-framework-for-internal-coding-agents)
