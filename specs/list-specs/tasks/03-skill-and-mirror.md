# Task 03: `/list-specs` SKILL.md + antigravity mirror + plugin bump

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Priority values run P0 (highest) through P3; the header is optional — absent means P2. -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers, in every task file — and ## Progress / ## Deferred questions are drain-written sections (single writer, main checkout): workers report that content, never write it. -->

Status: pending
Depends on: 02
Priority: P2
Budget: 10 turns
Spec: ../SPEC.md (Solution, Disambiguation, acceptance criterion on SKILL.md frontmatter)
Touch: .claude/skills/list-specs/SKILL.md, antigravity/.agents/skills/list-specs/SKILL.md, antigravity/.agents/skills/list-specs/list_specs.py, antigravity/.agents/skills/list-specs/test_list_specs.py, antigravity/.agents/skills/_shared/spec_readiness.py, antigravity/.agents/skills/_shared/test_spec_readiness.py, .claude-plugin/plugin.json

## Goal

`/list-specs` exists as a thin, model-invocable wrapper skill that runs
`list_specs.py` against the cwd and presents its stdout table as the
response — and this task is the spec's closing task, so it also lands the
antigravity mirror + plugin.json version bump for every file this spec
touched (CLAUDE.md's mirror convention: same commit, this is the
designated closing task).

## Touch

The seven paths above only. Do not re-implement `list_specs.py` or
`spec_readiness.py` logic here — Tasks 01/02 already landed those; this
task only copies them verbatim into the antigravity tree.

## Steps

1. Write `.claude/skills/list-specs/SKILL.md`. Frontmatter: `name:
   list-specs`; a `description:` stating what the skill does (per-repo
   spec status + next-command table) AND explicitly naming `/prioritize`
   as the "reorder work, not report the next command" alternative (the
   reciprocal half of the Disambiguation section in `../SPEC.md`); no
   `disable-model-invocation` field (this skill is read-only, stays
   model-invocable, per Solution); no `argument-hint` (R6: always cwd, no
   arguments). Body: run `python3 .claude/skills/list-specs/list_specs.py`
   against the cwd and present its stdout table as the response; note
   that it never auto-invokes the suggested next command (Out of scope).
   Close with a `Next stage:` line — this skill is terminal and must never
   self-chain (Out of scope explicitly forbids auto-invoking the
   suggested command), so write `Next stage: none — the table's Next
   command column names a per-spec next step; the human decides which to
   run.`
2. Read an existing model-invocable skill's antigravity mirror (e.g.
   `antigravity/.agents/skills/workboard/SKILL.md`) to match this repo's
   paraphrased-port conventions and frontmatter shape, then write a
   paraphrased (not verbatim) port to
   `antigravity/.agents/skills/list-specs/SKILL.md` covering the same
   description, disambiguation from `/prioritize`, and behavior.
3. Byte-copy the two files Task 02 landed into the antigravity mirror:
   `cp .claude/skills/list-specs/list_specs.py antigravity/.agents/skills/list-specs/list_specs.py`
   and the matching test file. Byte-copy the two files Task 01 landed:
   `cp .claude/skills/_shared/spec_readiness.py antigravity/.agents/skills/_shared/spec_readiness.py`
   and its test file. Confirm each pair with `diff -q`.
4. Run the mirrored test suites to confirm they pass identically:
   `python3 -m pytest antigravity/.agents/skills/list-specs/test_list_specs.py antigravity/.agents/skills/_shared/test_spec_readiness.py`.
5. Bump `.claude-plugin/plugin.json`'s `"version"` field (patch bump).
6. Commit the SKILL.md, the full antigravity mirror, and the plugin.json
   bump together — this is the single commit CLAUDE.md's mirror
   convention requires.

## Acceptance

- [ ] `grep -n "disable-model-invocation" .claude/skills/list-specs/SKILL.md` → no match.
- [ ] `grep -n "/prioritize" .claude/skills/list-specs/SKILL.md` → present in the frontmatter description.
- [ ] `grep -n "list_specs.py" .claude/skills/list-specs/SKILL.md` → the body invokes the script at the correct relative path (`.claude/skills/list-specs/list_specs.py`), not a typo'd or stale path — this is the only check that would catch a wrapper pointing at the wrong file, since Task 02's acceptance only runs the script directly.
- [ ] `diff .claude/skills/list-specs/list_specs.py antigravity/.agents/skills/list-specs/list_specs.py` → no output.
- [ ] `diff .claude/skills/list-specs/test_list_specs.py antigravity/.agents/skills/list-specs/test_list_specs.py` → no output.
- [ ] `diff .claude/skills/_shared/spec_readiness.py antigravity/.agents/skills/_shared/spec_readiness.py` → no output.
- [ ] `diff .claude/skills/_shared/test_spec_readiness.py antigravity/.agents/skills/_shared/test_spec_readiness.py` → no output.
- [ ] `grep -n "/prioritize" antigravity/.agents/skills/list-specs/SKILL.md` → the paraphrased mirror also carries the reciprocal disambiguation (content-coverage check, not a byte diff — this file is a paraphrased port).
- [ ] `python3 -m pytest antigravity/.agents/skills/list-specs/test_list_specs.py antigravity/.agents/skills/_shared/test_spec_readiness.py` → passes.
- [ ] `git diff HEAD~1 -- .claude-plugin/plugin.json` (once committed) shows the version field changed.
