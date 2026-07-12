# Task 03: closing — antigravity mirror + plugin bump (dfp)

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers. -->

Status: done
Depends on: 01, 02
Priority: P2
Budget: 3 turns
Spec: ../SPEC.md (requirement R5)
Touch: antigravity/.agents/workflows/drain.md, codex/.agents/skills/drain/SKILL.md, .claude-plugin/plugin.json

## Goal

Content-equivalent Intake-refused/assessor-contract updates land in the
antigravity drain workflow's stub-intake section; the codex drain wrapper
is checked — update only if its text embeds the affected stub-intake
clauses, else record "codex wrapper summarizes above this level" in the
commit message. Plugin version bumped RELATIVE to this task's base in
THIS task's own commit; validate + ultra-gate green.

## Acceptance

- [x] `grep -qi 'Intake-refused' antigravity/.agents/workflows/drain.md` → hit (0 today, verified)
  - Evidence: grep exits 0 (HIT); antigravity stub-intake now carries the R1 non-promotion bullet + section-6 audit line. codex mirror also updated (2 Intake-refused mentions) since its wrapper embeds the affected assess/act + section-6 clauses.
- [x] `claude plugin validate .` → passes AND `bash evals/lint-ultra-gate.sh` → OK
  - Evidence: `claude plugin validate .` → "✔ Validation passed"; `bash evals/lint-ultra-gate.sh` → "lint-ultra-gate: OK — all ultra mentions gated in 4 files".
- [x] `git show HEAD -- .claude-plugin/plugin.json | grep -q '^+.*"version"'` right after this task's commit → hit
  - Evidence: plugin.json bumped 0.8.46 → 0.8.47 in this task's own (HEAD) commit; grep matches the `+  "version": "0.8.47",` line.
- Verifier PASS on all three criteria + SPEC R5 mirror-intent; full report at specs/drain-forward-progress/evidence/03-mirror-bump.md.
