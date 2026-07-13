# Task 02: import agent-console, deduped against the skill tree

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Priority values run P0 (highest) through P3; the header is optional — absent means P2. -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers, in every task file — and ## Progress / ## Deferred questions are drain-written sections (single writer, main checkout): workers report that content, never write it. -->

Status: done
Depends on: none
Priority: P0
Budget: 30 turns
Spec: ../SPEC.md (requirements R2, R3, R4, R7)
Touch: agent-console/

## Goal

`agent-console/` exists at the repo root: a copy of `~/agent-console`'s
tracked files (minus `.git/`, minus nested `.claude/`) that lands ALREADY
deduped against the skill tree — no vendored `viz.py` (the server resolves
`.claude/skills/_shared/viz.py` from its own file location, env-var
overridable), no in-server scanner (`scan_specs`/`scan_tasks`/
`scan_handoffs`/`build_board` deleted; the `/workboard` route imports
`.claude/skills/workboard/workboard.py` and calls `assemble()` /
`attention_items()` / `ready_items()`), with a thin adapter mapping the
`assemble()` result (inbox items `severity/state/what/why/cmd/repo/age_ts`)
to the board shape `render_workboard` consumes (`sev/state/item/why/cmd/
repo/age`). `scripts/check.sh` is rewritten in the same change: the
`viz.py --self-sha256` / `# viz-sha256:` conformance block is removed and
the inline smoke test feeds a fixture `assemble()`-shaped dict through the
adapter into `render_workboard`, asserting the fixture repo name appears
in the rendered HTML.

## Touch

Only the new `agent-console/` tree. This task proves the spec's riskiest
assumption (the adapter seam). Read `.claude/skills/workboard/workboard.py`
and `.claude/skills/_shared/viz.py` freely but do NOT modify them —
`workboard.py`'s CLI contract (`--json`, `--out`, ROOTS, `--stale-days`,
`--abandon*`) and both files' contents are out of bounds (task 03 owns
skill-tree edits, and there are none planned). Do NOT touch `AGENTS.md`,
`antigravity/**`, or `.claude-plugin/**`. Do NOT modify the source repo at
`~/agent-console`. `render_workboard`'s output stays equivalent for
equivalent data — no visual/behavioral tab changes beyond the data seam.

## Steps

1. Copy `~/agent-console`'s tracked files at HEAD into
   `<repo>/agent-console/`, skipping `.claude/`; drop `viz.py` at copy
   time.
2. Write the failing smoke first: rewrite `scripts/check.sh`'s inline
   smoke test to the adapter seam (fixture `assemble()` dict → adapter →
   `render_workboard` → assert fixture repo name in HTML). Confirm it
   fails against the just-copied server.
3. In `agent-console.py`: add module resolution for the skill tree
   (derive `<repo>/.claude/skills/` from the server file's own path;
   env-var override for non-checkout layouts); import `viz` from
   `_shared` and `workboard` from the workboard skill dir.
4. Delete `scan_specs`, `scan_tasks`, `scan_handoffs`, `build_board`;
   write the adapter; point the `/workboard` route at
   `workboard.assemble()` (+ `attention_items()`/`ready_items()`) through
   the adapter.
5. Remove the conformance block from `scripts/check.sh`; update
   `tests/test_parsers.py` only where it referenced deleted functions.
6. `bash agent-console/scripts/check.sh` green; run the sweeps; commit.

## Acceptance

- [x] `bash agent-console/scripts/check.sh` → exit 0 — verifier PASS, evidence/02-import-agent-console-deduped.md
- [x] `test ! -f agent-console/viz.py && test ! -d agent-console/.claude` → exit 0 — verifier PASS
- [x] `grep -cE "viz-sha256|--self-sha256" agent-console/scripts/check.sh` → 0 — verifier PASS
- [x] `grep -cE "def (scan_specs|scan_tasks|scan_handoffs|build_board)" agent-console/agent-console.py` → 0 — verifier PASS
- [x] `grep -n "workboard" agent-console/agent-console.py | grep -c "import"` → ≥1 — verifier PASS
- [x] `python3 .claude/skills/workboard/workboard.py --json > /dev/null && python3 .claude/skills/workboard/workboard.py --out /tmp/wb-contract.html && test -s /tmp/wb-contract.html` → exit 0 (skill CLI contract untouched) — verifier PASS
- [x] `git diff --stat main -- .claude/skills/` → empty (no skill-tree edits) — verifier PASS
- [x] `grep -rn "sjaconette\|Jaconette" agent-console/ | wc -l` → 0 — verifier PASS
- [x] `find agent-console -name "*.plist" ! -name "*.tmpl" | wc -l` → 0 — verifier PASS

## Discovered

- [2026-07-05 /drain] Mutation-guard repo list can diverge from the workboard's repo list → tasks/05-mutation-guard-repo-divergence.md
- [2026-07-05 /drain] Workboard per-spec Priority select always shows unset → tasks/06-workboard-priority-select-unset.md
