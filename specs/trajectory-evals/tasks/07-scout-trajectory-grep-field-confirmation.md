Status: draft
Discovered-from: specs/trajectory-evals/evidence/spec-review.md
Spec: ../SPEC.md
Blocking: no

# confirm the real stream-json field shape for the scout-delegation trajectory grep

`evals/breakdown/02-scout-delegation/assert.sh` and the matching
`.claude/skills/evals/reference.md` example grep for the bare `"scout"`
value in the stream-json Task-input field, assumed from Claude Code's
documented format rather than confirmed against a real transcript. If
plugin agents surface namespaced (e.g. `"agentic:scout"`), the substring
match still works, but a differently-nested field could false-fail. Needs
a real `claude -p --output-format stream-json` run to confirm and, if
necessary, adjust the grep.

## Acceptance

- [ ] A capture record exists at
      `specs/trajectory-evals/evidence/stream-json-task-event.md` (no
      such file today, verified 2026-07-19) containing: the exact
      `claude -p --output-format stream-json` command run, the run date,
      and the verbatim JSONL Task-dispatch event line from that run —
      checkable as `[ -s <file> ]` plus
      `grep -q '"type"[[:space:]]*:[[:space:]]*"tool_use"' <file>` and
      `grep -q 'stream-json' <file>`. The capture run spawns a paid
      headless session: it is human-launched or orchestrator-run; a
      drained worker marks this criterion manual-pending with that
      reason (docs/memory/unattended-worker-tool-limits.md).
- [ ] Pattern-matches-reality (runnable, stays valid whether or not the
      grep gets adjusted): extracting the committed pattern from the
      assert script and running it against the captured event exits 0 —
      `pat=$(sed -n "s/^grep -Eq '\(.*\)' \"\$EVAL_TRANSCRIPT\".*/\1/p" evals/breakdown/02-scout-delegation/assert.sh); grep -Eq "$pat" specs/trajectory-evals/evidence/stream-json-task-event.md`
      — and the same extraction from
      `.claude/skills/evals/reference.md` yields the identical pattern:
      `[ "$pat" = "$(sed -n "s/^grep -Eq '\(.*\)' \"\$EVAL_TRANSCRIPT\".*/\1/p" .claude/skills/evals/reference.md)" ]`
      (both sed extractions confirmed working against today's files,
      verified 2026-07-19; cannot pass today because the evidence file
      does not exist). If the real field shape differs from the assumed
      one, the worker adjusts the grep in BOTH files — and, per
      CLAUDE.md's mirror convention, the inline
      `"subagent_type":"scout"` example carried by
      `codex/.agents/skills/evals/SKILL.md` — before this check runs.

Depth ceiling: the second criterion exercises the real pattern against
real transcript data (behavioral), but the evidence file's provenance —
that the event genuinely came from a live run rather than being typed —
is not machine-provable; complement is a manual-pending human
re-run/attestation of the capture command.
