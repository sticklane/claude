# Task 01: canonical resolution recipe in reference.md + bin/resolve-skill-path

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch, Rigor) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Priority values run P0 (highest) through P3; the header is optional — absent means P2. -->
<!-- Status vocabulary: pending → in-progress → done; also blocked (always with an Unblock: line), deferred, skipped, draft (stub awaiting promotion), and needs-verification (implementation complete, acceptance unverified — the verifier flips it to done; scanners treat it as open agent-bounded work, never a needs-attention flag). -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers, in every task file — and ## Progress / ## Deferred questions are drain-written sections (single writer, main checkout): workers report that content, never write it. -->

Status: in-progress
Depends on: none
Priority: P0
Budget: 20 turns
Spec: ../SPEC.md (requirements R1, R2, R3)
Touch: .claude/skills/drain/reference.md, bin/resolve-skill-path, tests/test_resolve_skill_path.sh

## Goal

`reference.md`'s Worker prompt section states the canonical two-step
plugin-path resolution recipe as a fenced, runnable Bash block (replacing
the vague "the plugin cache path found at dispatch" phrase at line 664),
and `bin/resolve-skill-path` implements the identical recipe as a
standalone script for the in-repo case, tested against a shimmed `claude
plugin list --json`.

## Touch

Do not touch `antigravity/.agents/workflows/drain.md` or
`codex/.agents/skills/drain/SKILL.md` — that's task 03. Do not touch any
`.claude/skills/*/SKILL.md` file other than referencing this task's
canonical section by citation from elsewhere — the repo-wide sweep is
task 02.

## Steps

1. Write the fenced Bash recipe in `reference.md`, replacing the vague
   phrase at line 664 (verify the line number against current content
   first — it may have shifted since this task was authored; locate by
   `grep -n "plugin cache path found at dispatch" .claude/skills/drain/reference.md`
   rather than trusting a hard-coded line number). Two steps, per the
   spec's Solution section: (1) check `.claude/skills/<skill>/<file>`
   exists relative to repo root — if yes, stop, that's the path; (2)
   resolve the installed version via `claude plugin list --json` (quote
   `bin/plugin-installed-version`'s existing parse logic rather than
   reinventing it), construct
   `$HOME/.claude/plugins/cache/agentic-toolkit/agentic/<version>/.claude/skills/<skill>/<file>`,
   verify it exists. Include this EXACT sentence verbatim in the recipe
   text (it is the pinned runtime-neutral procedural line task 03's
   mirror port and manifest entry both key off — must match character for
   character): "resolve once per session, never reuse a version number
   seen elsewhere in context."
2. Write a failing test first for `bin/resolve-skill-path`
   (`tests/test_resolve_skill_path.sh`, mirroring
   `tests/test_plugin_version_helper.sh`'s shim-based approach — stub
   `claude plugin list --json` output, never depend on a real installed
   plugin): in-repo path exists → returns it without calling the shim;
   in-repo absent, shim reports a version whose constructed path exists →
   returns that path; shim reports no matching plugin or the constructed
   path doesn't exist → exit 1 with non-empty stderr.
3. Implement `bin/resolve-skill-path <repo-relative-path>` to make the
   test pass: prints the resolved path on stdout, exits 0 on success,
   exits 1 with a stderr diagnostic naming what was tried on failure.
4. In `reference.md`'s recipe text, note explicitly that this script is
   the in-repo shortcut for the same two steps — never claims reachability
   from a non-toolkit repo pre-bootstrap.

## Acceptance

- [ ] `grep -c "plugin cache path found at dispatch" .claude/skills/drain/reference.md`
      → 0 (the vague phrase is gone).
- [ ] `grep -q "plugins/cache/agentic-toolkit/agentic" .claude/skills/drain/reference.md`
      → matches (the recipe's own content was added).
- [ ] `awk '/^```bash/,/^```$/' .claude/skills/drain/reference.md | grep -q "plugins/cache/agentic-toolkit/agentic"`
      → matches (the recipe literal lives inside an actual fenced Bash
      block, not bare prose).
- [ ] `[ -x bin/resolve-skill-path ]` — script exists and is executable.
- [ ] `bash tests/test_resolve_skill_path.sh` passes.
