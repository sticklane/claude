# Task 03: Mirror the widened procedure and bump plugin version

Status: pending
Depends on: 01
Priority: P1
Budget: 8 turns
Spec: ../SPEC.md (requirement R10)
Touch: antigravity/.agents/workflows/drain.md, codex/.agents/skills/drain/SKILL.md, .claude-plugin/plugin.json

## Goal

`antigravity/.agents/workflows/drain.md` and
`codex/.agents/skills/drain/SKILL.md` reflect the same widened cross-spec
admission procedure task 01 landed in `.claude/skills/drain/{SKILL.md,reference.md}`
(load-bearing runtime differences excepted, per this repo's
mirror-procedure-discipline), and `.claude-plugin/plugin.json`'s version is
bumped.

## Touch

Only the three files listed above. This task depends on task 01 completing
first — it mirrors task 01's landed prose, so it must not start (or its
mirrored content will be stale) until task 01's diff is on `main`. Do not
re-touch `.claude/skills/drain/SKILL.md` or `.claude/skills/drain/reference.md`
themselves (task 01's scope, already merged by the time this task starts).

## Steps

1. Read task 01's landed diff to `.claude/skills/drain/SKILL.md` and
   `.claude/skills/drain/reference.md` in full — this task ports that
   exact procedure, it does not re-derive it independently.
2. Per `.claude/rules/mirror-procedure-discipline.md`: classify each piece
   of the new cross-spec admission procedure as load-bearing (a runtime
   mechanism difference — leave as-is) or incidental (should carry over
   faithfully) before porting. Cite the rule rather than re-deriving its
   discipline.
3. Update `antigravity/.agents/workflows/drain.md` to reflect the same
   widened procedure — the up-to-3-spec-lease claim, the cross-spec
   Touch-disjointness admission layer, the two-level ≤5-per-spec/≤10-shared
   worker cap, and the spec-completion-review sibling-citation instruction
   (R7).
4. Update `codex/.agents/skills/drain/SKILL.md` (real content, not a
   symlink) with the same content-coverage — per
   `docs/memory/workboard-mirror-verbatim.md`, this is a paraphrased port,
   not a byte-identical diff; write a content-coverage check, not a diff
   check.
5. Bump `.claude-plugin/plugin.json`'s `version` field.

## Acceptance

- [ ] `grep -li "swarm\|cross-spec\|multi-spec" antigravity/.agents/workflows/drain.md codex/.agents/skills/drain/SKILL.md` → both files listed
- [ ] plugin.json version is greater than its value at this task's own base commit (compare via `git show <base-commit>:.claude-plugin/plugin.json`, never a hard-coded literal)
- [ ] `claude plugin validate .` → exits 0
- [ ] Every project gate this repo runs at merge time (`specs/status.sh`, every `tests/test_*.sh`, `./bin/check-agent-model-pins`, `evals/lint-ultra-gate.sh`, `evals/lint-skill-size-gate.sh`) exits 0
