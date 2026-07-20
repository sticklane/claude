# Task 03: Mirror the widened procedure and bump plugin version

Status: in-progress
Depends on: 01, 06
Priority: P1
Budget: 10 turns
Spec: ../SPEC.md (requirements R10, R15)
Touch: antigravity/.agents/workflows/drain.md, codex/.agents/skills/drain/SKILL.md, .claude-plugin/plugin.json

## Goal

`antigravity/.agents/workflows/drain.md` and
`codex/.agents/skills/drain/SKILL.md` reflect the same widened cross-spec
admission procedure task 01 landed in `.claude/skills/drain/{SKILL.md,reference.md}`
(load-bearing runtime differences excepted, per this repo's
mirror-procedure-discipline), AND task 06's `admission.py` live-invocation
rewiring — round-10 revision extended this task's scope and `Depends on:`
to cover both waves in one mirror pass rather than a second mirror task, so
this task now waits on task 06 landing (not just task 01) before starting.
`.claude-plugin/plugin.json`'s version is bumped.

## Touch

Only the three files listed above. This task depends on tasks 01 AND 06
completing first — it mirrors both their landed prose, so it must not start
(or its mirrored content will be stale/incomplete) until both diffs are on
`main`. Do not re-touch `.claude/skills/drain/SKILL.md` or
`.claude/skills/drain/reference.md` themselves, or `admission.py` (task
04/06's scope, already merged by the time this task starts).

## Steps

1. Read task 01's landed diff AND task 06's landed diff to
   `.claude/skills/drain/SKILL.md` and `.claude/skills/drain/reference.md`
   in full — this task ports both exact procedures, it does not re-derive
   either independently.
2. Per `.claude/rules/mirror-procedure-discipline.md`: classify each piece
   of the new cross-spec admission procedure AND the `admission.py`
   invocation as load-bearing (a runtime mechanism difference — leave
   as-is) or incidental (should carry over faithfully) before porting.
   Cite the rule rather than re-deriving its discipline. Note per this
   spec's own scouting: antigravity's drain surface is a workflow
   (`antigravity/.agents/workflows/drain.md`), which shells out to scripts
   directly (e.g. its `prioritize.md` workflow already runs `python3
   <dir>/prioritize_scan.py`) — the antigravity mirror of `admission.py`'s
   invocation is a direct shell-out, not a prose instruction to an agent;
   this is the load-bearing runtime-mechanism divergence, not incidental
   drift.
3. Update `antigravity/.agents/workflows/drain.md` to reflect the same
   widened procedure — the up-to-3-spec-lease claim, the cross-spec
   Touch-disjointness admission layer, the two-level ≤5-per-spec/≤10-shared
   worker cap, the spec-completion-review sibling-citation instruction
   (R7), AND task 06's `admission.py` invocation (as a direct shell-out per
   step 2's load-bearing classification).
4. Update `codex/.agents/skills/drain/SKILL.md` (real content, not a
   symlink) with the same content-coverage, including the `admission.py`
   invocation instruction (codex skills invoke scripts via prose, same
   mechanism as Claude Code) — per
   `docs/memory/workboard-mirror-verbatim.md`, this is a paraphrased port,
   not a byte-identical diff; write a content-coverage check, not a diff
   check.
5. Bump `.claude-plugin/plugin.json`'s `version` field.

## Acceptance

- [ ] Per-item, per-file content anchors (rewritten 2026-07-19: the
      original single `grep -li "swarm\|cross-spec\|multi-spec"` check let
      a partial port pass — one incidental mention per file green-checked
      all four ported items, against the memory doc's multi-file rule).
      For EACH of `antigravity/.agents/workflows/drain.md` and
      `codex/.agents/skills/drain/SKILL.md`:
      `grep -ci "cross-spec" <file>` → ≥ 1 (admission layer),
      `grep -ci "up to 3" <file>` → ≥ 1 (spec-lease claim),
      `grep -c "≤10\|<= 10" <file>` → ≥ 1 (two-level cap), and
      `grep -ci "already-green" <file>` → ≥ 1 (R7 sibling-citation
      instruction — the memory-doc phrasing task 01 adopts verbatim), and
      `grep -c "admission.py" <file>` → ≥ 1 (task 06's `admission.py`
      invocation, round-10 addition — absent from both files today,
      verified 2026-07-19).
      All five phrases absent from both files today, verified 2026-07-19.
      Depth ceiling: L0 anchors on a paraphrased port — behavioral
      complement is the closure-triggered cross-reference sweep
      (`.claude/rules/mirror-verification.md`) plus a verifier
      procedural-equivalence read of the ported sections against task 01's
      landed diff (`.claude/rules/mirror-procedure-discipline.md`).
- [ ] plugin.json version is greater than its value at this task's own base commit (compare via `git show <base-commit>:.claude-plugin/plugin.json`, never a hard-coded literal)
- [ ] `claude plugin validate .` → exits 0
- [ ] Every project gate this repo runs at merge time (`specs/status.sh`, every `tests/test_*.sh`, `./bin/check-agent-model-pins`, `evals/lint-ultra-gate.sh`, `evals/lint-skill-size-gate.sh`) exits 0
