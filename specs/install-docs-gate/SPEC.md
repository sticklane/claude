# Gate install-docs accuracy: README plugin names + antigravity setup paths

## Problem

README.md's install instructions (lines 107-178) are accurate today —
`/plugin marketplace add sticklane/claude` and
`/plugin install agentic@agentic-toolkit` correctly pair `.claude-plugin/
plugin.json`'s `name: "agentic"` with `marketplace.json`'s
`name: "agentic-toolkit"` — but nothing checks that this stays true. A
future rename of either name (a real risk: skill/plugin names do get
revised) would silently break every new user's first command with no
warning until someone tries it. Separately: the original ask mentioned
"antigravity-cli setup" — that isn't an actual documented concept in this
repo (its one mention, in `docs/agent-dashboards.md`, links to an
unrelated third-party tool). The real Antigravity install path is
`antigravity/README.md`'s manual copy steps
(`cp -r ~/agentic-toolkit/antigravity/.agents .` etc.), which this spec's
gate covers instead.

## Solution

A new test, `tests/test_install_docs.sh`, following this repo's existing
`tests/test_doc_links.sh` pattern (a plain bash script, auto-discovered by
the `for t in tests/test_*.sh; do bash "$t"; done` runner AGENTS.md's
Commands section already documents — no separate wiring). It checks:

1. Every `/plugin install <X>@<Y>` command in README.md has `<X>` equal to
   `.claude-plugin/plugin.json`'s `"name"` field and `<Y>` equal to
   `.claude-plugin/marketplace.json`'s `"name"` field.
2. Every `/plugin marketplace add <owner>/<repo>` command in README.md has
   `<owner>` matching `marketplace.json`'s `"owner"` field.
3. Every relative path `antigravity/README.md` tells a user to `cp` from
   or into (e.g. `antigravity/.agents`, `antigravity/AGENTS.md`) exists in
   this repo at that path.

## Requirements

- **R1**: `tests/test_install_docs.sh` extracts every
  `/plugin install <X>@<Y>` occurrence from README.md and fails with a
  message naming the exact mismatch if `<X>` != `plugin.json`'s
  **top-level** `"name"` field (the first `"name":` key at the top of the
  file — `plugin.json` also has an `author.name`, which must NOT be used)
  or `<Y>` != `marketplace.json`'s **top-level** `"name"` field (note:
  `marketplace.json` has a second, nested `plugins[0].name` field with a
  *different* value — the check must anchor on the top-level key only,
  not the first `"name":` match in the file).
- **R2**: Same script extracts every `/plugin marketplace add <owner>/<repo>`
  occurrence and fails if `<owner>` != `marketplace.json`'s `owner.name`
  field (`owner` is a nested object, `{"name": "sticklane", ...}` — not a
  scalar string field itself; the check compares against `owner.name`).
- **R3**: Same script extracts every path referenced in a `cp` command
  inside `antigravity/README.md`'s install section and fails if that path
  does not exist in the repo. Extraction must: strip the leading
  `~/agentic-toolkit/` clone-directory prefix (defined in README.md, not
  antigravity/README.md — the cp commands are written assuming that clone
  location) from each source operand, take only the source operand of
  each `cp` (never the `.` destination argument), and ignore trailing
  inline comments (e.g. `# merge if you have one`) — this guards the
  antigravity setup path the original ask was really about.
- **R4**: The script exits 0 with no output when everything matches (same
  convention as `tests/test_doc_links.sh`), and exits non-zero with a
  one-line-per-mismatch message otherwise.
- **R5**: No new test-runner wiring is added — the script's location and
  `test_*.sh` name are sufficient for the existing runner to pick it up
  (cite AGENTS.md:36, don't restate the runner).
- **R6**: The script accepts an optional first argument, a repo-root path
  (defaulting to its own location's repo root when omitted, resolved the
  same way `test_doc_links.sh` resolves paths from `BASH_SOURCE`) — this
  is the fixture-injection seam the acceptance criteria's "run against a
  fixture tree" checks rely on, rather than mutating-then-reverting the
  real repo's files in place.

## Out of scope

- Verifying the plugin/marketplace names actually resolve on a live
  Claude Code install (no network calls) — purely static cross-file
  consistency checks.
- Any change to the actual install instructions, `plugin.json`, or
  `marketplace.json` content — this is a gate, not a docs rewrite.
- Checking every other doc in the repo for staleness — scoped to
  README.md's install section and antigravity/README.md's setup section
  only.
- A general "antigravity-cli" integration — confirmed not a real concept
  in this repo; not built here.

## Acceptance criteria

- [ ] `bash tests/test_install_docs.sh` exits 0 against the current repo
      state (today's README.md/plugin.json/marketplace.json/antigravity
      files all already match).
- [ ] Fixture tree (a copy of the repo's relevant files under a tmp root)
      with `plugin.json`'s top-level `name` changed: running
      `bash tests/test_install_docs.sh <fixture-root>` (R6) fails, naming
      the mismatch (plugin.json's top-level name vs. README's `<X>`) —
      and does NOT false-fail by comparing against `author.name` instead.
- [ ] Same fixture mechanism with `marketplace.json`'s `owner.name`
      changed: fails, naming that mismatch — and does NOT false-fail by
      comparing README's `<X>`/`<Y>` against `marketplace.json`'s nested
      `plugins[0].name` instead of its top-level `name`.
- [ ] Same fixture mechanism with `antigravity/.agents` renamed/removed:
      fails, naming the missing path.
- [ ] `for t in tests/test_*.sh; do bash "$t"; done` (the existing runner)
      picks up and runs the new script with no additional configuration.

## Open questions

(none)
