# Task 01: Readiness computation + "Ready to start" section

Status: pending
Depends on: none
Priority: P0
Budget: 12 turns
Spec: ../SPEC.md (requirements R1, R2, R3; cross-cutting R8, R9)
Touch: .claude/skills/workboard/workboard.py, antigravity/.agents/skills/workboard/workboard.py, .claude-plugin/plugin.json, tests/test_workboard_actionability.sh, tests/fixtures/workboard-actionability/

## Goal
`workboard.py` parses a new `Depends on:` header and computes the set of
*ready-to-start* toolkit-spec tasks using drain's dispatchability rule, then
renders a visually distinct "Ready to start" section (count, one row per
item, empty state) into the existing static HTML. A new hermetic test file
covers the R1–R3 readiness assertions. Changes are mirrored to the
antigravity workboard in the same commit and `plugin.json` `version` is
bumped. This task establishes the fixture tree + test harness that tasks 02
and 03 extend.

## Touch
This task OWNS creation of `tests/fixtures/workboard-actionability/` and
`tests/test_workboard_actionability.sh` — tasks 02 and 03 only *extend* the
test file, never rewrite it. Do NOT touch the attention-inbox rendering
(`attention_items()` / its HTML) beyond what R3 needs to place the new
section; grouping/filter work belongs to task 03. Do NOT write the actions
script; that is task 02. Do not modify `attention_items()` cmd strings.

## Steps
1. **RED** — create `tests/fixtures/workboard-actionability/` with a toolkit
   fixture repo tree containing specs that exercise every R1 branch:
   - a spec with a pending task whose only dep is a **same-spec bare-numeric**
     id pointing at a `done` sibling (⇒ ready, single-ready ⇒ `/build`);
   - a spec whose pending task's dep is a **cross-spec `../`-relative path**
     to a `done` task in another fixture spec (⇒ ready — guards the case a
     same-spec-only rule would wrongly hide);
   - a spec whose pending task depends on a still-`pending` task (⇒ NOT ready);
   - a task with an **unresolvable** dep id (⇒ NOT ready, recorded
     blocked-by-unresolved with the offending id surfaced);
   - a spec with **≥2 ready tasks** (⇒ one `/drain specs/<slug>` item).
   Write `tests/test_workboard_actionability.sh`: export `HOME` and
   `CLAUDE_CONFIG_DIR` to the fixture tree, invoke
   `python3 .claude/skills/workboard/workboard.py <fixture-repos...> --out
   $tmp/wb.html --actions-out $tmp/a.sh` passing the fixture repo(s) as
   **explicit positional roots** (because `default_roots()` appends
   `Path.cwd()`, workboard.py:127). Assert the R1–R3 items from the spec's
   acceptance list. Run it; confirm it fails for the right reason (no "Ready
   to start" output yet), not a harness error.
2. **GREEN** — in `workboard.py`, extend the spec-task scanner (currently
   reads `Status:` at :173–218) to also parse `Depends on:`. Implement the
   dep-resolution exactly as drain does (SKILL.md:57–58): comma-split + trim;
   `none`/empty ⇒ ready; bare-numeric ⇒ sibling `NN-*.md` in the same spec;
   `../`-relative or `specs/...`-rooted path ⇒ another spec's task file
   resolved relative to the current task dir; `<slug>/NN` shorthand ⇒ expand
   to `../<slug>/tasks/NN-*.md` before resolving. A dep is satisfied when its
   resolved file is `Status: done`; unresolvable ⇒ NOT ready +
   blocked-by-unresolved with the offending id. Exclude Kiro/Antigravity
   specs (toolkit specs only).
3. Compute each ready item's `cmd` per R2: single ready task in a spec ⇒
   `cd <quoted-repo> && claude "/build specs/<slug>/tasks/<resolved-filename>.md"`
   (fully-resolved filename, not an `NN-*.md` glob); a spec with ≥2 ready
   tasks ⇒ one spec-level `cd <quoted-repo> && claude "/drain specs/<slug>"`.
   `<quoted-repo>` = absolute repo path, quoted.
4. Render the "Ready to start" section per R3 in the HTML template
   (:823–929): visually distinct from the attention inbox, showing a count
   and one row per item (repo · spec · task · `cmd`), rendered even when the
   inbox is empty, with a "nothing ready" empty state when zero.
5. **Mirror + bump (R9)** — port the same behavior to
   `antigravity/.agents/skills/workboard/workboard.py` (port equivalently if
   the mirror has diverged; note divergence in the commit message) and bump
   `version` in `.claude-plugin/plugin.json`.
6. Confirm the module still parses and the smoke run exits 0 (R8).

## Acceptance
- [ ] `bash tests/test_workboard_actionability.sh` → passes (R1–R3 subset:
      same-spec ready `/build`, cross-spec ready, pending-dep not ready,
      unresolvable → blocked-by-unresolved, ≥2-ready → `/drain`)
- [ ] `python3 -c "import ast; ast.parse(open('.claude/skills/workboard/workboard.py').read())"` → exits 0
- [ ] `python3 -c "import ast; ast.parse(open('antigravity/.agents/skills/workboard/workboard.py').read())"` → exits 0
- [ ] `python3 .claude/skills/workboard/workboard.py --out /tmp/wb.html --actions-out /tmp/wb.actions.sh` → exits 0 and `/tmp/wb.html` contains a "Ready to start" section header (R8, R3)
- [ ] `git diff --cached --name-only` (or `git show --stat` after commit) includes BOTH `workboard.py` paths and `.claude-plugin/plugin.json` (R9)
