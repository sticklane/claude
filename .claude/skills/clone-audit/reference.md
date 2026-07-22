# clone-audit reference

Per-stack clone-detection recipes for [SKILL.md](SKILL.md), plus one
non-normative worked example. Both recipes route through the same tool
(`jscpd`) so a mixed TS/Go repo needs one detector, not two.

## Table of Contents

- [TS/JS recipe](#tsjs-recipe)
- [Go recipe](#go-recipe)
- [Combined mixed-repo recipe](#combined-mixed-repo-recipe)
- [Reading the report](#reading-the-report)
- [Worked example: fooszone three-homography case (non-normative)](#worked-example-fooszone-three-homography-case-non-normative)

## TS/JS recipe

`jscpd` (fetched on demand via `npx`, no persistent install needed) tokenizes
TS/JS and reports clones by file + line range + duplicated-token count:

```bash
npx --yes jscpd --format typescript,javascript -r console,json -o <out-dir> <path>
```

`-r console,json` prints a human-readable table to stdout and also writes
`<out-dir>/jscpd-report.json` for programmatic parsing (a `duplicates` array,
each entry naming `firstFile`/`secondFile` with `name`, `start`, `end`).

## Go recipe

The same `jscpd` binary lists `go` as a supported format (`npx jscpd
--list`), so no second tool is required for the common case:

```bash
npx --yes jscpd --format go -r console,json -o <out-dir> <path>
```

If a repo needs Go-specific clone semantics `jscpd`'s generic tokenizer
doesn't capture (e.g. type-aware AST comparison), `dupl`
(`go run github.com/mibk/dupl@latest -t 50 <path>`) is the fallback — it
requires a working Go toolchain but no separate install step, matching the
"reachable without a persistent install" preference from this recipe's
originating task.

## Combined mixed-repo recipe

Both formats in one pass, since `jscpd` scans by format list, not by
per-language invocation:

```bash
npx --yes jscpd --format typescript,go -r console,json -o <out-dir> <path>
```

This is the exact command the in-repo rediscovery check
(`specs/ctx-static-analysis-augmentation/tests/clone-audit.sh`) runs against
the committed TS and Go fixture pairs
(`specs/ctx-static-analysis-augmentation/fixtures/clone-audit/`) to prove the
recipe actually rediscovers a known clone in both stacks.

## Reading the report

`jscpd-report.json`'s `duplicates` array is the source of truth; each entry
has `format`, `lines`, `tokens`, and a `firstFile`/`secondFile` pair (each
with `name`, `start`, `end`). Rank by `tokens` descending when reporting to a
human — a large duplicated-token count is a stronger signal than a large
line count alone (a long block of near-empty boilerplate can have many lines
but few tokens).

## Worked example: fooszone three-homography case (non-normative)

A live fooszone session (2026-07-20) hand-discovered three independent TS
homography implementations plus repeated Go CLI helpers (`drawLine` ×3,
`writeJSON` ×2) — exactly the class of duplication this recipe finds
mechanically. This example is recorded here for orientation only, not as a
normative fixture: whether a detector clusters a `.tsx` component with a
`.ts` module as one clone or two is threshold-dependent (`--min-tokens`,
`--min-lines`), so the exact clustering fooszone's homography files produced
is not something a future recipe run is expected to reproduce byte-for-byte.
The normative, asserted case is the committed in-repo TS/Go fixture pair
this skill's rediscovery check runs against — never this repo's drifting
contents.
