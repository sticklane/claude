# Task 03: Grouped, ranked inbox + clickable filter tiles

Status: in-progress
Depends on: 02
Priority: P1
Budget: 12 turns
Spec: ../SPEC.md (requirements R6, R7; cross-cutting R8, R9)
Touch: .claude/skills/workboard/workboard.py, antigravity/.agents/skills/workboard/workboard.py, .claude-plugin/plugin.json, tests/test_workboard_actionability.sh, tests/fixtures/workboard-actionability/

<!-- PLAN (delete at close-out)
Files, in order:
1. tests/test_workboard_actionability.sh — RED: append R6 (group headers in
   blocked→needs-review→stale order via python index check) + R7 (data-filter
   tile, filter-handler JS, existing #filter input still present).
2. tests/fixtures/workboard-actionability/toolkit-repo/specs/ — add blocked-task
   (Status: blocked task ⇒ blocked inbox item) and stale-open (pending no-dep,
   backdated in harness ⇒ stale inbox item) so all three categories exist and
   R6 ordering is meaningfully testable. Harness backdates stale-open files.
3. workboard.py — GREEN R6: render_inbox() groups items by state in fixed order
   blocked→needs-review→stale, age_ts newest-first within group, each group an
   h3.group-head[data-category] + table[data-category]; item row content/cmd
   unchanged. GREEN R7: render_filter_tiles() emits one .ftile[data-filter=cat]
   per present category among ready/blocked/needs-review/stale with its count;
   tag section.ready with data-category="ready"; add a second <script> filter
   handler (querySelectorAll('[data-category]'), toggle on re-click). Keep the
   existing copy-handler script and #filter input untouched.
4. Mirror to antigravity/.agents/skills/workboard/workboard.py (same edits);
   bump plugin.json version 0.7.10→0.7.11. Same commit.
What could go wrong: filter script braces must be doubled ({{}}) inside
TEMPLATE.format(); stale-open pending task also shows as ready (harmless — no
assertion forbids it); category filter scoped to categorized surfaces only
(ready section + inbox groups), leaving Repos/etc. visible by design.
-->

## Goal
The attention inbox renders under per-category headers in fixed severity
order (`blocked` → `needs-review` → `stale`), newest-first by `age_ts`
within each group, with item content and `cmd` strings unchanged. The
top-of-board summary renders one `data-filter="<category>"` tile per present
category (`ready`, `blocked`, `needs-review`, `stale`) with its count, and
embedded JS toggles a click-to-filter that hides non-matching
items/sections and restores on re-click — coexisting with the existing
text-filter input. The test file gains the R6/R7 assertions. Mirrored to
antigravity in the same commit with a `version` bump. This is the final
implementation task.

## Touch
Extend `tests/test_workboard_actionability.sh` with R6/R7 assertions; reuse
task 01/02 fixtures (add a fixture only if a needs-review item is not
already present). Preserve the existing text-filter JS (:912–913) and the
click-to-copy handler (:902–906) — both must still work. Do NOT alter
attention-item detection logic or `cmd` strings (R6/R8): only regroup and
reorder the render.

## Steps
1. **RED** — extend the test: assert the inbox HTML renders category group
   headers in `blocked`, then `needs-review`, then `stale` order (R6);
   assert the HTML contains a `data-filter="needs-review"` tile and the
   filter-handler JS, AND still contains the existing text-filter input
   (R7). Run; confirm it fails for the right reason.
2. **GREEN (R6)** — group `attention_items()` output under per-category
   headers in the fixed severity order `blocked` → `needs-review` → `stale`;
   within a group order by existing `age_ts` newest-first. Leave each item's
   content and `cmd` exactly as today.
3. **GREEN (R7)** — render summary tiles: one box per present category among
   `ready`, `blocked`, `needs-review`, `stale`, each showing its count and
   carrying `data-filter="<category>"`. Add embedded JS (no external
   request) so clicking a tile hides all items/sections not of that category
   and clicking the active tile (or an "all" affordance) restores the full
   view. Keep the existing text-filter input working alongside it.
4. **Mirror + bump (R9)** — port to the antigravity workboard in the same
   commit (port equivalently if diverged, note in commit message); bump
   `plugin.json` `version`.
5. Confirm no regression (R8): click-to-copy, text-filter, and the
   `--abandon`/`--abandon-stale` mutation path (:440–458) and default
   `--out` write (:967–972) still behave.

## Acceptance
- [ ] `bash tests/test_workboard_actionability.sh` → passes (full R1–R7)
- [ ] `/tmp/wb.html` from `python3 .claude/skills/workboard/workboard.py --out /tmp/wb.html --actions-out /tmp/wb.actions.sh` contains a `data-filter="needs-review"` tile, the filter-handler JS, AND the existing text-filter input (R7)
- [ ] The inbox HTML shows category group headers in `blocked` → `needs-review` → `stale` order (R6)
- [ ] `python3 .claude/skills/workboard/workboard.py --out /tmp/wb.html --actions-out /tmp/wb.actions.sh` → exits 0 (R8 smoke)
- [ ] The commit touches BOTH workboard paths and shows a `version` bump in `.claude-plugin/plugin.json` (`git diff HEAD~1 -- .claude-plugin/plugin.json`) (R9)
