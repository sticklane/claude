# Task 01: mechanical antigravity parity gate script + workflow-author exemption

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->
<!-- Priority values run P0 (highest) through P3; the header is optional — absent means P2. -->
<!-- Append-only for workers: a worker may flip only its own task's Status: line, tick acceptance checkboxes and add evidence-citation lines, and maintain its plan comment block. The text of Goal, Steps, Touch, Budget, and every acceptance criterion is read-only to workers, in every task file — and ## Progress / ## Deferred questions are drain-written sections (single writer, main checkout): workers report that content, never write it. -->

Status: in-progress
Depends on: none
Priority: P1
Budget: 24 turns
Spec: ../SPEC.md (requirements R1, R2, R3, R4, R5)
Touch: tests/test_antigravity_parity.sh, antigravity/README.md

## Goal

`tests/test_antigravity_parity.sh` exists and, run standalone or via
`for t in tests/test_*.sh; do bash "$t"; done`, exits 0 against the current
repo — confirming every directory under `.claude/skills/` (except
`_shared`) and every `.md` file under `.claude/agents/` is either mirrored
into `antigravity/.agents/skills/<name>/` or `antigravity/.agents/workflows/
<name>.md`, or explicitly exempted by a first-token-anchored row in
`antigravity/README.md`'s "What maps to what" table whose right cell
contains the literal string "Not ported". `antigravity/README.md` gains a
new row exempting `workflow-author` (its left cell begins with the
backticked token `` `workflow-author` ``, its right cell contains "Not
ported" plus the no-scripted-fan-out-primitive rationale). The gate checks
existence only, never content (R5) — no assertions about a mirrored
skill's behavior.

## Touch

Only `tests/test_antigravity_parity.sh` (new file) and
`antigravity/README.md` (one new table row). Do not touch any
`.claude/skills/**` or `antigravity/.agents/**` content — this task adds a
checker and an exemption record, it does not port or edit any skill.

## Steps

1. Read `antigravity/README.md`'s "What maps to what" table (around lines
   26-39) to confirm the exact `|`-delimited row format, and note the
   existing `fleet` row (already exempted, "Not ported") as a model for
   the new `workflow-author` row and as fixture material for step 4.
2. Write `tests/test_antigravity_parity.sh` (mirror `tests/test_doc_links.sh`'s
   internal shape only — `set -u`, a `pass`/`fail` counter, an `assert`
   helper — NOT its final output line. `test_doc_links.sh` always prints
   `pass: N fail: N`, even on success; this spec's R4 is stricter and
   explicitly requires "exits 0 with **no output**" on success, so this
   script must print nothing at all when every name is covered, and print
   only the uncovered names (one per line, or a single line naming them)
   when it isn't. Do not add a summary line — that would make Acceptance
   item 1 below fail):
   - List every directory directly under `.claude/skills/` except
     `_shared`, and the basename (without `.md`) of every file directly
     under `.claude/agents/`. This combined list is the set of names to
     check.
   - For each name, pass if `antigravity/.agents/skills/<name>/` exists OR
     `antigravity/.agents/workflows/<name>.md` exists.
   - Otherwise, search `antigravity/README.md`'s table for a row whose
     first `|`-delimited cell's **first delimited token** (the first
     backtick-quoted `` `...` `` span, or the first `/`-prefixed slash
     command token, whichever starts the cell) equals the name (with or
     without backticks/leading slash). A token appearing later in the
     cell does not count — this is the anchoring rule R2 requires, and the
     spec's own worked example (the self-chaining row) is the regression
     case: `/idea` and `/breakdown` appear inside that row's left cell but
     do not start it, so they must NOT match. Note that `idea` and
     `breakdown` both already have real ported counterparts, so the
     existence check above passes before the table is ever consulted for
     them — the anchoring logic is only exercised by a name with NO
     counterpart that happens to appear later (not first) in some row's
     left cell. Step 4 below adds a fixture that actually exercises this
     path; don't skip it.
     - If such a row exists AND its right (second) `|`-delimited cell
       contains the literal substring `Not ported`, the name passes as
       exempted.
     - Otherwise the name fails; print it as uncovered.
   - Exit non-zero if any name failed, listing all uncovered names; exit 0
     with no output otherwise.
3. Add a new row to `antigravity/README.md`'s table for `workflow-author`:
   left cell begins with the backticked token `` `workflow-author` ``,
   right cell contains the literal string "Not ported" and states the
   rationale from the spec's Solution section (no scripted fan-out
   primitive in Antigravity — its entire job is authoring
   `.claude/workflows/*.js` for the Claude-Code-specific `Workflow` tool).
4. Verify the fixture behaviors from the spec's acceptance criteria by
   hand before committing (temporarily edit, test, then revert the
   temporary edit — only the real `workflow-author` row addition should
   remain in the final diff):
   - Temporarily delete the `fleet` "Not ported" row and re-run the
     script: it must fail, naming `fleet`.
   - Temporarily create an empty `.claude/skills/zzz-test-skill/` dir with
     no antigravity counterpart and no exemption row, re-run: it must
     fail, naming `zzz-test-skill`. Remove the fixture dir afterward.
   - False-exemption regression (R2's core case — the two fixtures above
     never reach the table-matching code, since neither name matches any
     row at all): temporarily create an empty `.claude/skills/zzz-midcell/`
     dir with no counterpart, and temporarily append the token
     `` zzz-midcell`` to the END of an existing "Not ported" row's left
     cell (after that row's own first token, so `zzz-midcell` is present
     in the cell but does not start it). Re-run: the script must still
     fail and name `zzz-midcell` — proving the anchoring logic rejects a
     match that isn't the cell's first token, not just accept whatever
     appears anywhere in the cell. Revert both temporary edits afterward.
5. Run `bash tests/test_antigravity_parity.sh` and
   `for t in tests/test_*.sh; do bash "$t"; done` and confirm both are
   clean, then commit the new script and the README row as one commit
   (or a small number of atomic commits per the repo's commit
   conventions).

## Acceptance

- [ ] `bash tests/test_antigravity_parity.sh` → exit 0, no output
- [ ] `grep -n "workflow-author" antigravity/README.md` → shows the new
      row, left cell beginning with the token `` `workflow-author` ``,
      right cell containing "Not ported"
- [ ] Fixture check (run by hand, not left in the tree): temporarily
      removing `fleet`'s row and re-running the script fails and names
      `fleet`; restoring the row makes it pass again
- [ ] Fixture check (run by hand, not left in the tree): temporarily
      adding an empty `.claude/skills/zzz-test-skill/` with no counterpart
      or exemption row makes the script fail and name `zzz-test-skill`;
      removing the fixture dir makes it pass again
- [ ] Fixture check (run by hand, not left in the tree): temporarily
      adding an empty `.claude/skills/zzz-midcell/` with no counterpart,
      AND temporarily appending the token `zzz-midcell` to the end (not
      the start) of an existing "Not ported" row's left cell, makes the
      script fail and name `zzz-midcell` — confirming a non-first-token
      match is correctly rejected; reverting both edits makes it pass
      again
- [ ] `for t in tests/test_*.sh; do bash "$t"; done` → exits 0, picks up
      the new script automatically with no changes to the runner
