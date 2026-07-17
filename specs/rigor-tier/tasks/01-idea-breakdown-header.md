# Task 01: /idea writes the Rigor: header, /breakdown propagates it

Status: done
Depends on: none
Priority: P1
Budget: 8 turns
Spec: ../SPEC.md (requirements R1, R2, R3, R8)
Touch: .claude/skills/idea/SKILL.md, .claude/skills/breakdown/SKILL.md, antigravity/.agents/skills/idea/SKILL.md, antigravity/.agents/skills/breakdown/SKILL.md, CLAUDE.md

## Goal

`/idea`'s interview offers a prototype-vs-production choice and writes an
optional single-line `Rigor:` header (absent means `production`) into the
SPEC.md it produces, the same way `Priority:` is written. `/breakdown`
reads a spec's effective `Rigor:` and copies it onto every task file it
generates. Both antigravity mirrors carry the equivalent behavior.

## Touch

Do not touch `.claude/skills/build/SKILL.md`, `.claude/skills/drain/SKILL.md`,
`.claude/skills/list-specs/SKILL.md`, or `.claude/rules/quality-discipline.md`
— those belong to sibling tasks 02 and 03. Do not touch
`.claude-plugin/plugin.json` — the version bump is the closing task.

## Steps

1. In `.claude/skills/idea/SKILL.md`'s interview section, add one
   `AskUserQuestion` option set offering prototype vs. production (or
   equivalent single-question addition to an existing interview step);
   on "prototype", write `Rigor: prototype` as a single-line header above
   the produced SPEC.md's first `##` heading (same placement convention as
   `Priority:`). On "production" (or no answer), write nothing — absent
   means production per R1.
2. In `.claude/skills/breakdown/SKILL.md`'s task-file-generation step, read
   the source spec's effective `Rigor:` (absent = production) and write
   the same single-line header onto every generated task file.
3. Port both changes into `antigravity/.agents/skills/idea/SKILL.md` and
   `antigravity/.agents/skills/breakdown/SKILL.md` — paraphrased ports are
   fine (these are prose skills, not byte-identical mirrors); match the
   behavior, not the wording.
4. `CLAUDE.md`'s "Authoring conventions" bullet on machine-read headers
   ("Fields any skill reads programmatically — Status, Depends on,
   Priority ... Budget, and ... Touch") currently omits `Rigor:` even
   though it's now a fifth programmatically-read single-line header — add
   `Rigor` to that enumeration (absent = production) in the same commit
   this task establishes the header, so the convention doc doesn't drift
   from day one.
5. Run `bash evals/lint-ultra-gate.sh` before committing (idea/SKILL.md is
   an ultra-path skill).

## Acceptance

- [x] `grep -q "Rigor:" .claude/skills/idea/SKILL.md && grep -q "Rigor:" .claude/skills/breakdown/SKILL.md` — exit 0 (commit 94dde62) — verifier PASS (2026-07-16 sweep)
- [x] `grep -qi "rigor" antigravity/.agents/skills/idea/SKILL.md && grep -qi "rigor" antigravity/.agents/skills/breakdown/SKILL.md` — exit 0 — verifier PASS (2026-07-16 sweep)
- [x] `grep -qi "rigor" CLAUDE.md` — exit 0 — verifier PASS (2026-07-16 sweep)
- [x] `bash evals/lint-ultra-gate.sh` exits 0 — "OK — all ultra mentions gated in 4 files" — verifier PASS (2026-07-16 sweep)
- [ ] Manual, per CLAUDE.md's testing convention (mark evidence, don't
      block merge on it): fresh-session `/idea` a throwaway-tool pitch,
      answer "prototype" — the produced SPEC.md carries `Rigor: prototype`
      above its first `##`. — manual-pending: unattended worker cannot
      exercise a launch-gated /idea session interactively (AskUserQuestion
      unavailable to a background worker; unattended-worker-tool-limits doctrine).
