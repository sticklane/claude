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

## Solution

Rewrite the no-match path to (a) state the boundary and (b) hand the
agent the exact bounded content-check to run next. ctx does NOT run
the content scan itself: a whole-tree text scan at query time would
break the architecture rule that query work is never whole-tree, and
the calling agent already has a superior bounded grep. Print, don't
execute.

New no-match output (text mode; `--json` carries the same fields):

```
no symbol matches 'figureBboxes'
note: only definitions/references are indexed — object fields, JSON
keys, and string literals are not. Absence of a symbol is not absence
from code. To check text presence (bounded):
  grep -rl --include='*.{ts,tsx,go,py,js}' -m1 'figureBboxes' . | head -20
```

The suggested command is generated, not canned: the `--include` list
comes from the languages present in the index, the literal is the
queried name shell-escaped, and the bound (`-m1` + `head -20`) is
fixed — aligned with the bounded-extraction rules in
specs/shell-text-tool-doctrine.

## Requirements

- R1 — Every no-match result from `refs`, `sig`, and `show` (from
  specs/ctx-query-ergonomics) emits the three-part output: no-match
  line, boundary note, suggested bounded command. Golden tests pin all
  three parts, including shell-escaping of a name containing `$`/`'`.
- R2 — `--json` no-match returns
  `{matches: [], boundary_note: "...", suggested_check: "..."}` —
  empty `matches` is never the whole payload. Golden test.
- R3 — The suggested command's include-list derives from indexed
  languages (fixture with a two-language repo shows exactly those two
  extensions); the bound is present verbatim (`-m1`, `| head -20`).
- R4 — Near-miss help retained and extended: when case-insensitive or
  substring candidates exist in the symbol table, list up to 5 as
  "did you mean" BEFORE the boundary note (cheap — symbol-table only,
  no tree work). Golden test with a case-variant fixture.
- R5 — Docs: skill scope cautions' absence-fallacy entry
  (specs/ctx-skill-token-doctrine R7) is updated to say the tool now
  emits the guard itself, and the reading ladder's VERIFY ABSENCE
  guidance points at the emitted command; skill + antigravity mirror
  same-commit, respecting the Landing order.

## Non-goals

- A `ctx text <literal>` scanning subcommand (whole-tree query work —
  architecture rule; the agent's own Grep is the right executor).
- Fuzzy/semantic matching beyond R4's cheap near-miss list.
