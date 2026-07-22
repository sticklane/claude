Status: done
Discovered-from: spec-completion review (2026-07-21)
Spec: ../SPEC.md
Blocking: no

# `suggested_check`'s grep is not fixed-string, so regex-metacharacter symbols mismatch

The suggested bounded-grep command interpolates the raw symbol name as a
`grep` pattern (not `grep -F`), so a symbol containing regex
metacharacters isn't matched literally. The module's own test symbol
`a$b'c` renders as the regex `a$b'c` (`$` anchors end-of-line) and would
never match the literal text it's meant to check; a symbol containing
`(`/`[` could make grep error outright. Shell metacharacters are already
escaped; regex metacharacters are not. Low impact for plain identifiers
(the common case) — left unfixed by the reviewing worker because
plain-grep may be the intended behavior and changing it edits a shipped
acceptance shape.

## Fix

`suggested_check` now emits `grep -rlF` (fixed-string matching) instead of
`grep -rl`, so the symbol is matched as a literal, not a regex. `-F` is the
minimal, portable fix: it neutralizes every regex metacharacter at once
(`[`, `$`, `(`, `.`, `*`, …) without per-character escaping, and it composes
with the existing POSIX single-quote shell escaping that was already handling
shell metacharacters. The whole point of this module — telling an agent
whether a name is truly absent from the code — is defeated when a
metacharacter symbol makes grep error out (`a[b` → "brackets not balanced")
or silently mismatch: that yields a false "absent" verdict, the exact fallacy
the module exists to prevent.

`grep -rlF` was confirmed compatible with every shipped assertion: the three
integration surfaces (`tests/integration.rs` `starts_with("grep -rl")`,
`tests/query.rs` and `tests/mcp.rs` `contains("grep -rl")`) all remain
satisfied because `grep -rlF` still begins with / contains `grep -rl`. So no
documented acceptance shape changed — this is a strict compatibility-preserving
fix, not a contract change, and no DEFER was warranted.

## Acceptance

- [x] `suggested_check` emits a fixed-string grep (`grep -rlF`):
  `cd context-tree && grep -q 'grep -rlF' src/cmd/no_match.rs`
- [x] Regression test proves a regex-metacharacter symbol is matched literally
  — the new `suggested_check_matches_regex_metacharacter_symbols_literally`
  runs the produced command over a temp file whose text is the literal symbol
  (`a[b`, `a$b'c`) and asserts the file is found. It is RED on the pre-fix
  `grep -rl` command (`a[b` → grep "brackets not balanced", empty stdout) and
  GREEN on `grep -rlF`:
  `cd context-tree && cargo test --lib suggested_check_matches_regex_metacharacter_symbols_literally`
- [x] The existing suggested-check tests (extension-union, shell-escape) and
  the three integration surfaces asserting the `grep -rl` prefix stay green:
  `cd context-tree && bash scripts/check.sh` (fmt + clippy -D warnings + all
  tests) exits 0.
