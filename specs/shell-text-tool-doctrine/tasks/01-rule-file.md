# Task 01: Author the shell-text-tools rule file

Status: done
Depends on: none
Priority: P0
Budget: 8 turns
Spec: ../SPEC.md (requirements R1, R4)
Touch: .claude/rules/shell-text-tools.md, specs/shell-text-tool-doctrine/evidence/

## Goal

`.claude/rules/shell-text-tools.md` exists (≤60 lines) codifying when agents
use dedicated Read/Edit/Glob/Grep tools versus shell text tools, covering
points (a)-(e) from R1. The R4 mirror-parity finding (rules are NOT mirrored to
antigravity/codex — no rules dir exists there) is recorded in an evidence note,
and no mirror is created.

## Steps

1. Write `.claude/rules/shell-text-tools.md` (≤60 lines) with all five points:
   (a) writes to source/docs go through Edit/Write, never `sed -i` / in-place
   `awk` / `cat >`/`>>` onto tracked files — enumerate the documented
   exceptions: formatter-reflow .md heredoc case (per-repo, fooszone CLAUDE.md
   precedent) and generated/derived files (eval-sandbox fixtures);
   (b) reads of a file you will edit use Read;
   (c) shell text tools are for read-only extraction with BOUNDED output —
   every example caps via `head`, `grep -l/-m/-c`, `sed -n` ranges, or `awk`
   anchored ranges;
   (d) acceptance-command authoring: anchor greps to structure (function/section
   ranges, line-starts like `^## `, frontmatter extraction via
   `sed -n 's/^description: *//p'`) rather than file-wide literals — cite the
   doc-comment collision class;
   (e) cross-reference gate's deny-rule pairing (gate/reference.md) and
   token-discipline's delegation default.
2. Record the R4 finding in
   `specs/shell-text-tool-doctrine/evidence/r4-mirror-parity.md`: rules are not
   mirrored to antigravity/ or codex/ (verified: neither tree has a rules dir),
   so no mirror rides this change.

## Acceptance

- [x] `test -f .claude/rules/shell-text-tools.md` → exit 0
- [x] `test "$(wc -l < .claude/rules/shell-text-tools.md)" -le 60` → exit 0 (53 lines)
- [x] `grep -c 'sed -i' .claude/rules/shell-text-tools.md` → ≥1 (point a) — 3
- [x] `grep -ci 'read' .claude/rules/shell-text-tools.md` → ≥1 (point b) — 8
- [x] `grep -ci 'head\|-m\|-c\|sed -n\|awk' .claude/rules/shell-text-tools.md` → ≥1 (point c bounded output) — 13
- [x] `grep -c '\^## ' .claude/rules/shell-text-tools.md` → ≥1 (point d anchoring) — 1
- [x] `grep -ci 'gate\|token-discipline' .claude/rules/shell-text-tools.md` → ≥1 (point e) — 5
- [x] `test -f specs/shell-text-tool-doctrine/evidence/r4-mirror-parity.md` → exit 0
