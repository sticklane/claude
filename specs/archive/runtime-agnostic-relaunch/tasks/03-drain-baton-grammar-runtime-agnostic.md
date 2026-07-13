# Task 03: `drain/reference.md` baton grammar goes runtime-agnostic

Status: done
Depends on: 01
Priority: P2
Budget: 20 turns
Spec: ../SPEC.md (requirements R6, R7, R11)
Touch: .claude/skills/drain/reference.md

## Goal

The "Baton pass (self-relaunch)" section of `drain/reference.md` (currently
~lines 759-876) no longer hardcodes the literal `nohup claude -p "..." &`
template (~lines 855-862). Instead it instructs: resolve the repo's active
runtime (`.claude/runtime.md`, default `claude-code`), fetch that runtime's
template via `runtimes/parse_headless.py` (task 01 — the literal path
`runtimes/parse_headless.py` must appear in this section), substitute the
real `/drain <spec> (generation G+1, baton: ...)` prompt plus the project's
allowlist/turn-cap into the template's `<prompt>` placeholder, and wrap the
result in drain's own fixed POSIX backgrounding wrapper (`nohup … &`,
unchanged — this wrapper is drain-level orchestration, not part of the
runtime's contract, per SPEC.md's Solution section). When the parser
returns `NONE` (Antigravity today), the grammar renders a plain-language
instruction instead of a shell command: "No scriptable relaunch for
`<runtime>` — reopen generation G+1 from `<runtime>`'s Agent Manager,
pointed at `DRAIN-BATON.md`." The existing pointer at ~lines 704-708 (which
already said "other runtimes substitute their profile's Headless template"
but wasn't followed by the baton section) is reconciled so both sections
agree — either the baton section now matches that pointer's own claim, or
the pointer gets a forward-reference to the rewritten baton section.

## Touch

Doc-only change to `.claude/skills/drain/reference.md`. Do not touch
`.claude/skills/workboard/workboard.py` (task 02) or `evals/run.sh` (task
04) — disjoint files, no shared code. Do not touch
`antigravity/.agents/workflows/drain.md` — per scout research, Antigravity's
baton section is a deliberate, already-correct paraphrase ("an Antigravity
run cannot self-relaunch `claude`, so the human re-launches /drain from the
Agent Manager") that doesn't need updating for this change; it already says
the human-driven thing this task's `NONE` case also says.

## Steps

1. Read the current baton grammar section (~lines 759-876) and the pointer
   at ~lines 704-708 in `.claude/skills/drain/reference.md`.
2. Rewrite the hardcoded `nohup claude -p "..."` block (~855-862) into
   prose + a template-shaped description: resolve runtime → call
   `runtimes/parse_headless.py <runtime>` → substitute `<prompt>` →
   wrap in the fixed `nohup … &` backgrounding wrapper. Keep the
   `--allowedTools`/`--max-turns` substitution guidance — those are
   drain-level values inserted into the runtime template's own flag
   placeholders, not new backgrounding behavior.
3. Add the no-scriptable-relaunch (`NONE`) case: plain-language instruction,
   no shell command, referencing the runtime name and Agent Manager.
4. Edit the ~704-708 pointer paragraph so it accurately describes the
   rewritten section below it (no more "says the right thing but isn't
   followed" gap).
5. Leave the `DRAIN_RELAUNCH_CMD` override section (~870-875) untouched in
   meaning — it remains the explicit human-set escape hatch, unaffected by
   this spec (SPEC.md's Problem section is explicit that this override
   stays untouched).

## Acceptance

- [x] `sed -n '/## Baton pass/,/## Critique intake/p' .claude/skills/drain/reference.md | grep -c 'nohup claude -p "\/drain'` → `0`
- [x] `sed -n '/## Baton pass/,/## Critique intake/p' .claude/skills/drain/reference.md | grep -c 'runtimes/parse_headless.py'` → `1` or more
- [x] `grep -c 'DRAIN_RELAUNCH_CMD' .claude/skills/drain/reference.md` → unchanged from before this task (override section still present, still describes a verbatim escape hatch)
- [x] Manual read-through: the ~704-708 pointer and the rewritten baton
      section describe the same runtime-resolution rule (no contradiction)
