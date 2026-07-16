# Spec-completion review — trajectory-evals

spec review: 0 findings, 0 fixed, 1 discovered

Ref range: c596bd8c1bdae18f69c86dfb58f6dac2f534c6f8..main, restricted to the
union Touch of tasks 01-04 (evals/run.sh, evals/breakdown/, .claude/skills/evals/SKILL.md,
.claude/skills/evals/reference.md, codex/.agents/skills/evals/SKILL.md,
antigravity/.agents/workflows/evals.md, .claude-plugin/plugin.json,
specs/trajectory-evals/evidence/).

No high-confidence correctness/behavior findings. Verified: `EVAL_TRANSCRIPT`
is reset per loop iteration, set only on the claude-code non-dry-run branch,
guarded/cleared-with-warning when the transcript is absent or empty, and
exported only outside dry-run; the new scenario's `assert.sh` fails loudly
on an empty/missing transcript before any grep and is `set -u`-safe; no
existing `assert.sh` reads `session.log`, so the plaintext→stream-json
switch breaks no prior artifact-only scenario. All gates green:
`./specs/status.sh`, `bash evals/runner-selftest.sh`,
`bash evals/lint-ultra-gate.sh`, `claude plugin validate .`, and the full
`tests/test_*.sh` sweep (14 files).

Discovered (uncertain, not fixed):

- `evals/breakdown/02-scout-delegation/assert.sh:42` (and the matching
  `.claude/skills/evals/reference.md` example) assumes the stream-json
  Task-input value is the bare `"scout"`; a namespaced value (e.g.
  `"agentic:scout"`) would still substring-match, but a differently-nested
  field could false-fail. Unconfirmable without a live transcript — see
  specs/trajectory-evals/tasks/07-scout-trajectory-grep-field-confirmation.md.
