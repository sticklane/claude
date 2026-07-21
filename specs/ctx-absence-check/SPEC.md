# ctx: no-match output that prevents the absence fallacy

Serves CUJ: VERIFY ABSENCE (docs/guides/ctx-cujs.md).

Breakdown-ready: true

## Problem

A `ctx refs`/`sig` no-match means "no SYMBOL by that name" — object
fields, JSON keys, and string literals are not indexed — but the
output (`no symbol matches 'X'`) reads like "X is gone". That reading
produced a real spec error (fooszone, 2026-07-20: `figureBboxes`
asserted absent on ctx evidence while alive as object keys inside
`migrateLabel`, caught only by adversarial critique). Doctrine-side
mitigation landed (specs/ctx-skill-token-doctrine R7's absence-fallacy
caution), but Steven's directive (2026-07-21) is to fix it IN THE
TOOL: the failure happened at the point of output, so the guard
belongs at the point of output.

Seam with specs/ctx-dead-code-zones (one sentence, mirrored there):
"no-match" means SYMBOL RESOLUTION FAILED; a symbol that resolves but
whose results are emptied by filters (`--live-only`, `--in`,
`--zone`) is NOT a no-match and emits that spec's filter tail, never
this boundary output.

## Solution

Rewrite the no-match path to (a) state the boundary and (b) hand the
agent the exact bounded content-check to run next. ctx does NOT run
the content scan itself: a whole-tree text scan at query time would
break the architecture rule that query work is never whole-tree, and
the calling agent already has a superior bounded grep. Print, don't
execute.

New no-match output (text mode):

```
no symbol matches 'figureBboxes'
note: only definitions/references are indexed — object fields, JSON
keys, and string literals are not. Absence of a symbol is not absence
from code. To check text presence (bounded):
  grep -rl --include='*.ts' --include='*.tsx' --include='*.go' 'figureBboxes' . | head -20
```

The suggested command uses REPEATED `--include` flags — one per
extension — never brace expansion (`--include='*.{ts,go}'` matches
nothing in BSD/GNU grep's fnmatch and would mechanize the very
fallacy this spec kills; verified live 2026-07-21). The extension
list derives from the indexed languages via each language's extractor
extension list (one language may contribute several extensions, e.g.
typescript → .ts,.tsx); the literal is shell-escaped; the bound is
`| head -20` (`-m1` is omitted — it is a no-op with `-l`, which
already stops per-file at first match).

Contract-change blast radius (all surfaces named): text no-match
today prints one line to STDERR with a nonzero exit — the boundary
note + suggested command are APPENDED to stderr, stdout stays empty,
and the exit code is unchanged (scripts keying on it are unaffected).
JSON no-match today returns `{"error": "no match", "symbol": …}` —
the shape is EXTENDED, never replaced:
`{"error": "no match", "symbol": …, "boundary_note": "...",
"suggested_check": "..."}`. The MCP server (cli.rs `Mcp`, shared
`render()`) carries the same extended fields; both CLI and MCP
surfaces are covered by the goldens (this repo's own two-surface
precedent).

## Requirements

- R1 — `refs` and `sig` no-match emit the three-part output (no-match
  line, boundary note, suggested bounded command) per the surface
  contract above. `show` (specs/ctx-query-ergonomics R2) gets the
  same treatment IN THE SAME TASK THAT LANDS `show` or a later one —
  this spec's tasks must not reference `show` before it exists
  (ordering: after query-ergonomics R2). Golden tests pin all three
  parts on stderr, empty stdout, unchanged exit code, and
  shell-escaping of a name containing `$`/`'`.
- R2 — `--json` no-match returns the EXTENDED existing error object
  (`error`, `symbol`, `boundary_note`, `suggested_check`) — golden
  test asserts the legacy keys survive unchanged. An MCP-surface test
  asserts the same fields arrive through the MCP path.
- R3 — The suggested command's include-list derives from indexed
  languages via the extractor extension mapping: fixture with two
  indexed languages asserts exactly the union of those languages'
  extension lists appears as repeated `--include` flags; the bound
  `| head -20` is present verbatim; no brace pattern appears
  (`grep -c '{' suggested_check` = 0 in the JSON golden).
- R4 — Near-miss help ADDED (new behavior — verified 2026-07-21: the
  no-match paths in cmd/sig.rs:76, cmd/refs.rs:107, cmd/notes.rs
  print one line and exit; candidate listings exist only on the
  AMBIGUOUS branch; there is nothing to retain): when
  case-insensitive or substring candidates exist in the symbol table,
  list up to 5 as "did you mean" BEFORE the boundary note (cheap —
  symbol-table only, no tree work). Golden test with a case-variant
  fixture.
- R5 — Docs: skill scope cautions' absence-fallacy entry (authored by
  specs/ctx-skill-token-doctrine R7 — hard dependency, R7 lands
  first) is updated to say the tool now emits the guard itself, and
  the VERIFY ABSENCE ladder guidance points at the emitted command.
  This holds SLOT 6 of the SKILL.md editor registry in
  token-doctrine's Landing order; skill + antigravity mirror
  same-commit.

## Non-goals

- A `ctx text <literal>` scanning subcommand (whole-tree query work —
  architecture rule; the agent's own Grep is the right executor).
- Fuzzy/semantic matching beyond R4's cheap near-miss list.
- Changing no-match exit codes or stdout/stderr routing.

## Parallelization

All three tasks are sequential — no concurrent-safe groups. Task 02
extends task 01's same files (shared `no_match.rs` helper, `sig.rs`,
`refs.rs`) rather than being Touch-disjoint from it. Task 03 depends on
both for content accuracy (it describes the emitted command) and is
additionally externally blocked on specs/ctx-skill-token-doctrine R7.
