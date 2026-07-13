# Task 02: Mirror `screen-stub.sh` and fix `drain.md`'s stale `.claude/` references

Status: done
Depends on: none
Priority: P0
Budget: 8 turns
Spec: ../SPEC.md (items #2, #5)
Touch: antigravity/.agents/skills/drain/ (new directory), antigravity/.agents/workflows/drain.md

## Goal

`antigravity/.agents/workflows/drain.md`'s stub-intake deterministic
prompt-injection screen has a real, runnable mirrored script backing it
(not a dependency on a `.claude/`-only path), and its two rules-file
references point at the corresponding `AGENTS.md` sections instead of
nonexistent `.claude/rules/*.md` paths. `drain` is disable-model-invocation
and otherwise workflow-only in the mirror (no other file has
`antigravity/.agents/skills/drain/` today) — the new directory must read
as intentional script-bundle support for the workflow, not an incomplete
skill port.

## Touch

Only `antigravity/.agents/workflows/drain.md` and the new
`antigravity/.agents/skills/drain/` directory. Do not touch
`antigravity/.agents/skills/prioritize/` (task 03 owns that) or any of
the four files task 01 owns.

## Steps

1. Copy `.claude/skills/drain/screen-stub.sh` verbatim to
   `antigravity/.agents/skills/drain/screen-stub.sh` (the script has no
   internal `.claude/`-rooted references itself — confirm this while
   copying; if it does, that's new information, stop and flag it rather
   than silently rewriting the script's own logic).
2. Add `antigravity/.agents/skills/drain/README.md` stating this directory
   is a script bundle for `antigravity/.agents/workflows/drain.md`, not a
   triggerable skill (`drain` is `disable-model-invocation: true` at its
   `.claude/skills/drain/SKILL.md` source — no `SKILL.md` belongs here).
3. In `antigravity/.agents/workflows/drain.md`'s stub-intake section
   (~line 663), update the reference from
   `.claude/skills/drain/screen-stub.sh` to the new mirrored path
   `.agents/skills/drain/screen-stub.sh`.
4. In the same file, line 84: change the `.claude/rules/concurrent-sessions.md`
   citation to point at `AGENTS.md`'s "Concurrent sessions" section
   (`antigravity/AGENTS.md:147`).
5. In the same file, line 181: change the `.claude/rules/token-discipline.md`
   citation to point at `AGENTS.md`'s "Dispatch authoring" section
   (`antigravity/AGENTS.md:61`).

## Acceptance

- [x] `find antigravity -iname "screen-stub*"` → finds
      `antigravity/.agents/skills/drain/screen-stub.sh`
- [x] `diff .claude/skills/drain/screen-stub.sh antigravity/.agents/skills/drain/screen-stub.sh` → no output (verbatim mirror)
- [x] `grep -n 'screen-stub' antigravity/.agents/workflows/drain.md` → shows `.agents/skills/drain/screen-stub.sh`, no `.claude/`-rooted path
- [x] `grep -n '\.claude/rules' antigravity/.agents/workflows/drain.md` → no output
- [x] `ls antigravity/.agents/skills/drain/` → contains `screen-stub.sh` and `README.md`; no `SKILL.md`
- [x] `bash tests/test_antigravity_parity.sh` → exits 0
