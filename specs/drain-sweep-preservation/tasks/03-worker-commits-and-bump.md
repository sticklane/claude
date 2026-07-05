# Task 03: Incremental worker commits + version bump (R3, R4)

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Priority values run P0 (highest) through P3; the header is optional — absent means P2. -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers, in every task file — and ## Progress / ## Deferred questions are drain-written sections (single writer, main checkout): workers report that content, never write it. -->

Status: pending
Depends on: 02
Priority: P2
Budget: 6 turns
Spec: ../SPEC.md (requirements R3, R4)
Touch: .claude/skills/drain/reference.md, .claude-plugin/plugin.json, README.md

## Goal

Both drain worker prompts instruct incremental commits, and the plugin
version reflects the whole spec's change. The reference.md Worker prompt and
the Headless fallback prompt each gain the clause "commit to the task branch
at each completed TDD step (test → feat → refactor)" — the literal fragment
"at each completed TDD step" must appear in both. The Worker prompt (which
spawns a verifier; headless does not) additionally gains: always commit the
implementation "before spawning any verifier" or review pass — never hold the
full implementation uncommitted at close-out. `.claude-plugin/plugin.json`
version is bumped one patch level from its current value (0.8.8 at spec time;
re-read at build time). There is no CHANGELOG.md; add a README note only if
the repo's release convention (check recent bump commits via `git log
--oneline -- .claude-plugin/plugin.json`) shows one.

## Touch

reference.md worker-prompt sections only — do not edit the rescue procedure
(task 01) or the Environment kill subsection (task 02). SKILL.md is not
touched by this task.

## Steps

1. Add the incremental-commit clause to the reference.md Worker prompt
   (blockquote section "Worker prompt (verbatim, fill the <>)"), including
   the verifier-specific sentence with the literal "before spawning any
   verifier".
2. Add the incremental-commit clause (WITHOUT the verifier sentence — the
   headless allowlist has no Task tool and spawns nothing) to the Headless
   fallback prompt string.
3. Bump `.claude-plugin/plugin.json` version; follow whatever release-note
   convention the bump-commit history shows.
4. Run the acceptance commands from the repo root.

## Acceptance

- [ ] `[ "$(grep -c 'at each completed TDD step' .claude/skills/drain/reference.md)" -eq 2 ]` → true (Worker prompt + Headless fallback)
- [ ] `[ "$(grep -c 'before spawning any verifier' .claude/skills/drain/reference.md)" -eq 1 ]` → true (Worker prompt only)
- [ ] `grep -q '"version"' .claude-plugin/plugin.json && ! grep -q '"version": "0.8.8"' .claude-plugin/plugin.json` → version bumped from spec-time 0.8.8 (adjust mentally if the base moved; the point is a bump lands with this spec)
- [ ] `claude plugin validate .` → green
- [ ] `./specs/status.sh` → parses, no errors
