# Critique findings — harness-audit

Verdict: NOT READY (drain gen 7 critique intake, 2026-07-12)

1. **Delivery shape is an unresolved open question, but this spec feeds /breakdown
   next (conf 88).** Spec (lines 42-43, 82-83) defers "new skill vs /onboard re-run
   mode" to /critique. Touch paths + mirror obligation differ entirely: a new skill
   creates `.claude/skills/<name>/` + `antigravity/.agents/skills/<name>/`; an /onboard
   re-run mode edits the existing onboard SKILL.md + mirror. /breakdown cannot write
   concrete disjoint `Touch:` blocks or a closing mirror/bump task without this.

2. **AC1/AC2 not runnable — literal placeholders (conf 87).** Line 70
   `grep -qi "read-only" <the shipped skill/mode file>` (path unknown); line 72 uses
   `...` stubs naming only 2 of 5 areas. A drained worker cannot self-verify; stalls or
   passes vacuously. Root cause is finding 1 (target file undecided).

3. **AC greps not verified absent from current file state (conf 80).** No
   `grep -c → 0` confirmation possible because the file isn't named/created. Redo at
   breakdown against the created path (anchored-acceptance-criteria convention).

4. **R1 read-only contradicts the "Command currency" check (conf 76).** Line 47
   mandates "makes no edits, installs nothing" yet the checklist (25-26) runs every
   verified AGENTS.md command — routinely build/deploy/migrate commands that mutate.
   Needs explicit scope: which command classes are executed vs inspected.

5. **Acceptance almost entirely manual/placeholder for a drained worker (conf 78).**
   AC3 is interactive fresh-session (manual, ok); AC1/AC2 unrunnable stubs; only AC4
   (plugin.json bump + mirror) machine-checkable. Add at least one runnable behavioral
   check (audit run against a fixture repo asserting a seeded finding).

Non-blocking: R5/AC4 correctly require antigravity mirror + plugin.json bump; new skill
is not ultra-path so no lint-ultra-gate criterion owed — both correct.
