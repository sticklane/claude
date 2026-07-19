Status: draft
Discovered-from: specs/trajectory-evals/tasks/03-docs-and-codex-mirror.md
Spec: ../SPEC.md
Blocking: no

# codex evals mirror omits teardown.sh scenario-file bullet

codex/.agents/skills/evals/SKILL.md's scenario-file list omits the
.claude leg's teardown.sh bullet entirely (pre-existing procedural
divergence, not introduced by task 03) — a mirror-procedure-discipline
gap worth reconciling.

## Acceptance

- [ ] `grep -c 'teardown.sh' codex/.agents/skills/evals/SKILL.md` ≥ 1
      (0 today, verified 2026-07-19), the bullet landing inside the
      scenario-file list and carrying the source's stated conditions —
      optional; runs whenever setup.sh was attempted, pass or fail; a
      teardown failure fails the scenario (mirror-procedure-discipline:
      same conditions, not a bare mention). Codex runs the same
      `evals/run.sh`, which already executes teardown.sh, so this
      omission is incidental, not load-bearing.
- [ ] `tests/mirror-procedure-manifest.txt` gains the line
      `.claude/skills/evals/SKILL.md|codex/.agents/skills/evals/SKILL.md|teardown.sh`
      (no codex-evals entry exists today, verified 2026-07-19) and
      `bash tests/test_mirror_procedure_coverage.sh` exits 0 (green
      today, verified 2026-07-19 — the seeded line plus the bullet keep
      it green; the line alone without the bullet turns it red).
- [ ] Guard: antigravity's teardown.sh omission stays — it is
      re-confirmed load-bearing in the manifest's `# checked: evals`
      comment (no automated runner there), so no criterion here touches
      `antigravity/.agents/workflows/evals.md`.

Depth ceiling: both checks are text-presence/manifest greps — the
behavioral complement is a human-launched `./evals/run.sh` run of a
scenario shipping a `teardown.sh`, confirming the codex-documented flow
matches the runner (paid headless, human-only per
docs/memory/unattended-worker-tool-limits.md; manual-pending for a
drained worker).
