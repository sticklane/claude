# Task 03: Mark `prioritize/` as workflow-support and fix its stale spec comment

Status: in-progress
Depends on: none
Priority: P1
Budget: 5 turns
Spec: ../SPEC.md (items #3, #6)
Touch: antigravity/.agents/skills/prioritize/prioritize_scan.py, antigravity/.agents/skills/prioritize/README.md (new)

## Goal

`antigravity/.agents/skills/prioritize/` no longer reads as an
incomplete/half-populated skill port. It has a `README.md` stating it's a
script bundle for `antigravity/.agents/workflows/prioritize.md` (mirroring
task 02's `skills/drain/` treatment) and no `SKILL.md` (prioritize is
`disable-model-invocation: true` at its `.claude/skills/prioritize/SKILL.md`
source, so it must stay non-triggerable here too). `prioritize_scan.py`'s
docstring no longer implies the source toolkit's own `specs/prioritize/SPEC.md`
ships inside a standalone Antigravity install.

## Touch

Only the two paths listed above. Do not touch
`antigravity/.agents/skills/prioritize/test_prioritize_scan.py` (task 01
owns that file) or `antigravity/.agents/workflows/prioritize.md`.

## Steps

1. Add `antigravity/.agents/skills/prioritize/README.md` stating this
   directory is a script bundle for
   `antigravity/.agents/workflows/prioritize.md`, not a triggerable skill.
2. In `antigravity/.agents/skills/prioritize/prioritize_scan.py:18`, drop
   or reword the docstring comment `See specs/prioritize/SPEC.md (R1, R2)
   for the requirements this implements.` so it doesn't imply that spec
   exists in a standalone Antigravity consumer's `specs/` — e.g. reword to
   name the source toolkit repo explicitly ("this implements the
   requirements from the source toolkit's specs/prioritize/SPEC.md") or
   remove the sentence if the surrounding docstring reads fine without it.
3. Confirm no `SKILL.md` exists or was added in this directory.

## Acceptance

- [ ] `ls antigravity/.agents/skills/prioritize/` → contains `README.md`;
      no `SKILL.md`
- [ ] `grep -n 'specs/prioritize/SPEC.md' antigravity/.agents/skills/prioritize/prioritize_scan.py` → either no output, or output that no longer reads as if that spec ships with the mirror
- [ ] `cd antigravity/.agents/skills/prioritize && python3 -m pytest -q` → 17 passed
