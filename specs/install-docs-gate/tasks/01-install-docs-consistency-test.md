# Task 01: install-docs consistency gate test

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Priority values run P0 (highest) through P3; the header is optional — absent means P2. -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers, in every task file — and ## Progress / ## Deferred questions are drain-written sections (single writer, main checkout): workers report that content, never write it. -->

Status: pending
Depends on: none
Priority: P0
Budget: 20 turns
Spec: ../SPEC.md (requirements R1, R2, R3, R4, R5, R6)
Touch: tests/test_install_docs.sh

## Goal

`tests/test_install_docs.sh` exists, following `tests/test_doc_links.sh`'s
shape (plain bash, `BASH_SOURCE`-relative path resolution, `pass:`/`fail:`
summary line, non-zero exit on any failure). Run with no argument against
this repo it exits 0 silently on the success path; run against a fixture
tree with any of the three cross-file facts broken, it fails naming the
exact mismatch. The script requires no new test-runner wiring — its
`tests/test_*.sh` name and location are enough for the existing
`for t in tests/test_*.sh; do bash "$t"; done` sweep (AGENTS.md:36) to pick
it up.

## Touch

Only `tests/test_install_docs.sh` (new file). Do not edit README.md,
antigravity/README.md, `.claude-plugin/plugin.json`,
`.claude-plugin/marketplace.json`, or any other test file — this task adds
a gate, it does not touch the content the gate checks (spec's "Out of
scope"). Fixtures for the acceptance criteria are throwaway `mktemp -d`
trees built and torn down inside the task's own verification, never
committed.

## Steps

1. Write the failing skeleton first: a script that always fails (or an
   empty `pass:0 fail:1`), confirm it fails when run, then implement the
   three checks incrementally, re-running after each.
2. **R6 seam first** (everything else depends on it): accept an optional
   `$1` repo-root, defaulting via the same `BASH_SOURCE`-relative
   resolution `tests/test_doc_links.sh` uses (`here="$(cd "$(dirname
   "${BASH_SOURCE[0]}")" && pwd)"`, then `repo_root="$here/.."`). All file
   reads (README.md, antigravity/README.md, plugin.json,
   marketplace.json) resolve under `$repo_root`, not hardcoded paths.
3. **R1**: extract every `/plugin install <X>@<Y>` occurrence from
   `$repo_root/README.md` (regex on the literal command text). Read
   `$repo_root/.claude-plugin/plugin.json`'s top-level `"name"` field —
   anchor on the first `"name":` key at the top level (e.g. via a JSON
   parse if `jq` is available with a documented bash-only fallback that
   does NOT match inside a nested object like `author`); compare against
   `<X>`. Read `marketplace.json`'s top-level `"name"` similarly; compare
   against `<Y>`. On mismatch, print one line naming which side (plugin
   name vs marketplace name) and the two differing values.
4. **R2**: extract every `/plugin marketplace add <owner>/<repo>`
   occurrence from README.md; compare `<owner>` against
   `marketplace.json`'s nested `owner.name` field (not a top-level
   scalar). On mismatch, print one line naming the mismatch.
5. **R3**: extract `antigravity/README.md`'s install section's `cp`
   commands; take only the source operand of each `cp` (never the `.`
   destination), strip a leading `~/agentic-toolkit/` prefix if present,
   strip trailing inline `#` comments, and check the resulting path
   exists under `$repo_root`. On a missing path, print one line naming it.
6. Wire the three checks' pass/fail into the same `pass=`/`fail=`
   counter + `assert` pattern `test_doc_links.sh` uses; final line
   `pass: $pass fail: $fail`; `exit 1` if `fail > 0` else `exit 0`.
7. Build the three fixture trees the acceptance criteria need (copy the
   relevant files into a `mktemp -d` tree, mutate one fact each: (a)
   plugin.json's top-level name, (b) marketplace.json's owner.name, (c)
   remove/rename `antigravity/.agents`), run the script against each with
   the repo-root argument, confirm each fails naming the right mismatch
   and does NOT false-fail on the two documented "wrong field" traps
   (`author.name`, `plugins[0].name`).
8. Run the full `for t in tests/test_*.sh; do bash "$t" || exit 1; done`
   sweep to confirm no interference with existing tests, then commit.

## Acceptance

- [ ] `bash tests/test_install_docs.sh` → exit 0, `fail: 0` (today's
      README.md/plugin.json/marketplace.json/antigravity files already
      match)
- [ ] A fixture tree with `plugin.json`'s top-level `name` changed: `bash
      tests/test_install_docs.sh <fixture-root>` → non-zero exit, output
      names the plugin-name mismatch, and does not instead compare against
      `author.name`
- [ ] A fixture tree with `marketplace.json`'s `owner.name` changed: `bash
      tests/test_install_docs.sh <fixture-root>` → non-zero exit, output
      names that mismatch, and does not instead compare against the nested
      `plugins[0].name`
- [ ] A fixture tree with `antigravity/.agents` renamed/removed: `bash
      tests/test_install_docs.sh <fixture-root>` → non-zero exit, output
      names the missing path
- [ ] `for t in tests/test_*.sh; do bash "$t" || exit 1; done` → exit 0
      (new script picked up with no runner changes)
- [ ] `git diff --name-only main` → only `tests/test_install_docs.sh` (plus
      this task file)
