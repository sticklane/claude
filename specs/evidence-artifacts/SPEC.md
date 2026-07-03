# Persisted verification evidence

## Problem

The verifier's evidence — the commands it ran and what they printed —
lives only in its final message and dies with the session. Pull requests
then carry claims ("verified ✓") instead of proof. Both the Anthropic
playbook ("pull requests… verified end to end, it has screenshots for
me") and Antigravity's artifact model (docs/external-playbooks.md,
"Evidence artifacts") treat persisted evidence as what makes walk-away
trust possible.

## Solution

Evidence-writing is caller-directed: the verifier agent gains the `Write`
tool and writes its full report to a file **only when the invoking skill
passes an evidence path**; /build derives that path and commits the file
with the code. Invocations without a path (ad-hoc checks, ranking duty in
drain tournaments) never write. Files touched:
`.claude/agents/verifier.md`, `.claude/skills/build/SKILL.md`,
`.claude/skills/drain/SKILL.md`, `.claude/skills/drain/reference.md`,
and the antigravity mirrors `antigravity/.agents/skills/verifier/SKILL.md`,
`antigravity/.agents/workflows/build.md`,
`antigravity/.agents/workflows/drain.md`.

## Requirements

- R1: `.claude/agents/verifier.md` frontmatter `tools:` gains `Write`,
  and the body states: when the caller provides an evidence file path,
  write the full report to it, creating parent directories; when no path
  is provided, write nothing and do not derive one yourself.
- R2: the evidence FILE is the full record — verdict line, per-criterion
  entry with the exact command and an output tail (last ~10 lines), gate
  results, scope-creep findings. The chat MESSAGE keeps the existing
  under-a-page summary format and ends with a pointer to the evidence
  path (the file and the message are explicitly different lengths; the
  agent's output budget applies to the message only).
- R3: `.claude/skills/build/SKILL.md` step 3 passes the evidence path
  when spawning the verifier, derived as: task file matching
  `specs/<slug>/tasks/<name>.md` → `specs/<slug>/evidence/<name>.md`;
  bare spec at `specs/<slug>/SPEC.md` → `specs/<slug>/evidence/spec.md`;
  any other layout → no path (verifier writes nothing; close-out notes
  evidence was not persisted). Close-out commits the evidence file with
  the code and task file, and the task file's per-criterion evidence
  lines cite the `evidence/` file rather than duplicating output.
- R4: a re-verify overwrites the evidence file (latest verdict wins);
  stale PASS evidence from an earlier attempt must not survive a FAIL.
- R5: antigravity mirrors: `antigravity/.agents/skills/verifier/SKILL.md`
  adopts the same caller-provided-path rule and file/message split;
  `antigravity/.agents/workflows/build.md` passes the path and commits
  the file; both mention the `evidence/` directory by that literal name.
  The workflow notes Antigravity's native walkthrough artifacts
  complement but don't replace the committed file.
- R6: /drain needs no dispatch-side change for background workers — the
  evidence file is committed on the worker's branch by /build's
  close-out and arrives via the merge. `.claude/skills/drain/SKILL.md`
  gains one clause: DONE merges from background workers carry the
  `evidence/` file. `.claude/skills/drain/reference.md`'s headless
  fallback gains one line: headless merges carry no evidence file (no
  verifier ran inside the worker; the orchestrator's post-merge
  acceptance re-run is the record, and it should be pasted into
  `specs/<slug>/evidence/<name>.md` by the orchestrator before flipping
  to done). `antigravity/.agents/workflows/drain.md` mirrors the
  background-worker clause.

## Out of scope

- Screenshots or browser recordings (the verifier is CLI-only in v1;
  command output only).
- Evidence retention/pruning policy — files accumulate with the spec and
  are cleaned up when the spec directory is.
- Verifier-side path derivation of any kind (the caller decides; this
  is what keeps tournament-ranking invocations from clobbering evidence
  in the main checkout).
- plugin.json version (owned by the hardening-quick-wins spec).

## Acceptance criteria

- [ ] `grep -q "tools:.*Write" .claude/agents/verifier.md && grep -qi "when the caller provides" .claude/agents/verifier.md` (R1)
- [ ] verifier.md names the file contents (verdict, command + output tail, gates, scope creep) and states the message stays under a page with a pointer to the file: `grep -q "evidence" .claude/agents/verifier.md && grep -qi "output tail" .claude/agents/verifier.md` (R2)
- [ ] `grep -q "evidence/" .claude/skills/build/SKILL.md` — path derivation in step 3 and the commit instruction in close-out both present (R3)
- [ ] `grep -qi "overwrit" .claude/agents/verifier.md` (R4)
- [ ] `grep -q "evidence/" antigravity/.agents/skills/verifier/SKILL.md && grep -q "evidence/" antigravity/.agents/workflows/build.md` (R5)
- [ ] `grep -q "evidence/" .claude/skills/drain/SKILL.md && grep -q "evidence/" .claude/skills/drain/reference.md && grep -q "evidence/" antigravity/.agents/workflows/drain.md` (R6)
- [ ] End to end: run /build on a toy task at `specs/demo/tasks/01-toy.md` in a scratch repo; after close-out, `test -f specs/demo/evidence/01-toy.md` and `git log --stat -1` shows it committed (manual until the eval harness covers /build).

## Open questions

(none)
