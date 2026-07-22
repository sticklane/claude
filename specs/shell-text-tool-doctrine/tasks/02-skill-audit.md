# Task 02: Audit skill-embedded shell text commands

Status: in-progress
Depends on: 01
Priority: P1
Budget: 12 turns
Spec: ../SPEC.md (requirement R2)
Touch: .claude/skills/**/SKILL.md, .claude/skills/**/reference.md, specs/shell-text-tool-doctrine/evidence/

## Touch

May adjust embedded read-shaped grep/sed/awk examples in the 11 skill files to
be bounded per R1(c). Must NOT add the R3 pointer lines to idea/breakdown/
critique SKILL.md (that is Task 03) — this task only fixes/annotates existing
command usages. Must NOT touch the rule file (Task 01).

## Steps

1. Sweep `.claude/skills/**/SKILL.md` and `reference.md` for embedded
   sed/awk/grep/cat commands (11 files: evals, breakdown, idea, drain, gate,
   workflow-author, build, ctx).
2. For each usage classify verdict: ok / bounded-fix / write-violation.
   Every WRITE-shaped usage (`sed -i`, `cat >` onto a tracked file) is removed,
   converted to an Edit/Write instruction, or annotated as a documented R1
   exception (evals/reference.md `cat >` builds eval-sandbox fixtures =
   generated-files exception; gate/reference.md `sed -i` is deny-rule advice
   text, not a usage). Every read-shaped example is bounded per R1(c).
3. Mirror-affected files follow .claude/rules/mirror-procedure-discipline.md
   (none of the 11 are rule mirrors; skill mirrors in antigravity/ ride the
   same-commit mirror rule only if a SKILL.md's embedded command changes).
4. Write the sweep as a table (file, line, verdict) to
   `specs/shell-text-tool-doctrine/evidence/r2-sweep.md`. A silent "all fine"
   without the table fails R2.

## Acceptance

- [ ] `test -f specs/shell-text-tool-doctrine/evidence/r2-sweep.md` → exit 0
- [ ] `grep -Ec 'ok|bounded-fix|write-violation' specs/shell-text-tool-doctrine/evidence/r2-sweep.md` → ≥11 (one row per swept file)
- [ ] `grep -rnE 'sed -i|cat >' .claude/skills/ --include=SKILL.md --include=reference.md | grep -v 'evals/reference.md' | grep -v 'gate/reference.md'` → no unannotated write-shaped usage remains
