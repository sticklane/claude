# Critique findings — retire-static-dashboards (NOT READY)

Recorded by drain critique intake, gen 6, Run-token e83f34f07094a4fa, 2026-07-12.
Critic verdict: **NOT READY**. Fix these, then re-run /critique to earn `Breakdown-ready: true`.

## 1. [BLOCKER, conf 92] Recursive `grep -rn '.claude/'` sweeps transient worktrees — non-deterministic, unpassable

R1 (SPEC.md:62-63) and the acceptance criterion (SPEC.md:153-158) anchor on
`grep -rn '\bfleet\b' .claude/ antigravity/ docs/ AGENTS.md CLAUDE.md .claude-plugin/`.
The recursive `.claude/` arm descends into `.claude/worktrees/` (10 live worktrees = full repo
copies). Measured: **2524** `fleet` matches under `.claude/worktrees/` vs **9** git-tracked.
The AC "shows only (a)/(b)/(c)" can never hold in the main checkout, and the R1 inventory varies
run-to-run. Smallest fix: replace every recursive `grep -rn`/`grep -rl` over `.claude/` with
`git grep -n` (auto-excludes worktrees) or add `--exclude-dir=worktrees`, in R1 and the AC.
Single-file greps (SPEC.md:144-150, 161-164) are fine as-is.

## 2. [conf 78] Two closing ACs gate on tools an unattended drain worker cannot use, no manual-pending path

- SPEC.md:170-173 ("running `/fleet` in a session with a background agent prints the markdown table,
  no file written") requires an attended session with live harness TaskList + skill invocation —
  a drained worker has none. Mark explicit manual-pending per
  docs/memory/unattended-worker-tool-limits.md.
- SPEC.md:167-169 names `bash evals/run.sh`, the paid model-session eval runner (`/evals`,
  `disable-model-invocation: true`); CLAUDE.md forbids drained tasks gating on it. Zero
  fleet/--out/--emit-fleet-css fixtures exist under evals/ (vacuous anyway). Reword to a static
  `git grep` over the evalset fixtures.

## 3. [conf 65] R1 edits drain/SKILL.md (ultra-path) but no AC requires the ultra-gate

R1 (SPEC.md:71) rewords .claude/skills/drain/SKILL.md:366. `drain` is one of the four ultra-path
skills; CLAUDE.md mandates `bash evals/lint-ultra-gate.sh` before committing. No AC carries it.
Low risk (prose far from any "ultra" marker) but the obligation is unstated. Add an AC:
`bash evals/lint-ultra-gate.sh` exits 0.

## Verified clean (no finding)

R6 mirror obligations complete (codex/antigravity drain artifacts carry no `fleet` reference, so the
drain edit needs no counterpart); all eight R1 prose anchors present; workboard/viz/fleet single-file
anchors all present as claimed; plugin.json 0.8.48 makes R7's bump satisfiable.

## Triage 2026-07-13 (attended; Steven approved REVISE)

Verdict: REVISE (smallest of the batch). Edits before re-critique: (1) replace the recursive greps with `git grep` in R1 and the AC; (2) mark the `/fleet` e2e criterion manual-pending and swap `evals/run.sh` for a static `git grep` over eval fixtures; (3) add `bash evals/lint-ultra-gate.sh` as an AC. Verified: not superseded — fleet/reference.md still exists; workboard.py still carries render_html/--out/--actions-out (lines 2444, 2841, 2915).

## Re-critique 2026-07-13 (drain critique intake, run b4adb88f) — still NOT READY, approved plan not yet applied

`git log -- specs/retire-static-dashboards/SPEC.md` shows no commit since
the triage above — SPEC.md is byte-identical to the state that produced
this file's prior NOT READY verdict. Skipping a redundant full critic
dispatch on unchanged content per token-discipline's "cheap before
expensive" — the three approved triage edits above (smallest of the batch)
are the recovery path, unchanged. This spec's critique intake is spent for
this run.

## Re-critique (commit bc44f206, attended, not previously recorded here) — still NOT READY

The three approved triage edits landed in `bc44f20` ("fix: apply approved
REVISE edits to retire-static-dashboards SPEC.md"), and that commit's own
message records an immediate re-critique that surfaced three further gaps,
never carried into this file until now:

1. `fleet/SKILL.md`'s own stale HTML-snapshot frontmatter `description`
   untouched by R1/R2.
2. R6's antigravity mirror miscounts stale `fleet view`/`fleet's status
chips` references in workboard's mirror.
3. The sweep AC's "named in R1" whitelist clause doesn't cover legitimate
   unrelated prose R1 doesn't enumerate.

Not fixed at the time — only the three originally-approved edits were
authorized for that pass.

## Re-critique 2026-07-14 (drain critique intake, gen 3, run c92aedb1ae49f8d3) — still NOT READY

Independently re-verified all three originally-approved fixes (git grep
determinism — 68 deterministic tracked matches, zero worktree pollution;
manual-pending wording; the lint-ultra-gate AC) — all confirmed landed and
accurate. Also independently re-confirmed the three gaps `bc44f20`'s
message admitted but this file never recorded, ranked by cost-if-missed:

1. **Closing sweep AC is unsatisfiable — workboard code comments cite the
   deleted `fleet/reference.md`, and R6 miscounts them (confidence 88).**
   R2 deletes `.claude/skills/fleet/reference.md`, but both trees'
   workboard code has live comments pointing at it
   (`.claude/skills/workboard/workboard.py:2244,2634`,
   `antigravity/.agents/skills/workboard/workboard.py:2244,2245,2252,2634`,
   plus `antigravity/.../reference.md:80`, `.../SKILL.md:59`, and
   `test_workboard.py` in both trees — roughly 10 antigravity-side
   mentions, not R6's claimed "two remaining"). None are in the sweep AC's
   allowed set (a)/(b)/(c), so the sweep AC can never pass, and no
   requirement directs a worker to touch or whitelist them. Fix: add a
   requirement (and matching whitelist clause) covering the workboard
   status-chip comments in both trees; correct R6's count.
2. **Sweep AC whitelist is under-inclusive (confidence 82).**
   `docs/agent-dashboards.md:100` ("a fleet view is a safety control, not
   just per-agent logs") is generic prose not in R1's exempt list or the
   sweep AC's (a)/(b)/(c) set — fails the AC even after all correct edits.
   Fix: broaden clause (b) to cover legitimate unrelated "fleet" prose
   generally, not only phrases R1 happens to enumerate.
3. **`fleet/SKILL.md` frontmatter `description` still advertises the HTML
   snapshot (confidence 72).** Line 3 reads "...as a self-contained HTML
   snapshot with status tiles, a timeline, and per-agent detail" — none of
   that survives the change. R2 only requires "no longer contains an
   HTML-rendering step"; nothing directs rewriting the frontmatter
   description, the skill's actual auto-invocation trigger surface. Fix:
   add to R2 "and rewrite the SKILL.md frontmatter description to describe
   the inline markdown-table output."

Recovery: fix findings 1-3, then re-run /critique. This spec's critique
intake is spent for this run (Run-token c92aedb1ae49f8d3) — recorded in
`DRAIN-BATON.md`'s `Intake-failed:` line.

## Fix applied 2026-07-14 (attended, human-authorized HUMAN.md cleanup pass)

All three findings fixed directly in SPEC.md, re-verified live against the
current tree:

1. Rather than enumerating every dangling `fleet/reference.md` citation by
   file/line (fragile — this file is under active concurrent development,
   and the exact set already drifted once per the finding's own "10, not
   2" count), added a general requirement to R1/R6: every comment/
   docstring anywhere in both the `.claude` and `antigravity` trees
   (`workboard.py`, `test_workboard.py`, `reference.md`, `SKILL.md`) that
   cites the deleted `fleet/reference.md` path is reworded to stop citing
   it. Backed by a mechanical, count-independent AC:
   `git grep -rn 'fleet/reference\.md' -- .claude/ antigravity/` → 0
   matches (confirmed 4 today, across both trees).
2. Broadened the sweep AC's whitelist clause (b) to accept any generic
   "fleet-style"/"fleet convention"/"fleet's status chip(s)" phrasing
   describing workboard's reused visual convention, not only the specific
   instances R1 names — this also covers `docs/agent-dashboards.md`'s
   generic "fleet view" prose, and is necessary for the AC to stay
   satisfiable after finding 1's own fix rewords citations but leaves the
   "fleet-style" phrase itself in place.
3. R2 now requires `fleet/SKILL.md`'s frontmatter `description` be
   rewritten (its actual auto-invocation trigger surface, not just body
   prose). Added AC: `grep -c "self-contained HTML snapshot"
.claude/skills/fleet/SKILL.md` → 0 (confirmed 1 today).

Ready for re-critique.

## Re-critique 2026-07-14 (attended, /critique) — one new finding, R4 scope gap

A fresh critic dispatch flagged four findings, but three (the whitelist
narrowness, the antigravity mention count, the frontmatter AC) turned out
to already be fixed by the "Fix applied 2026-07-14" pass above — verified
directly against the live tree (the current whitelist clause (b) already
covers "fleet's status vocabulary"-style phrasing generically, and the
frontmatter AC already exists at SPEC.md:173-177). The critic appears to
have misread the already-broadened text; no action needed on those three.

The fourth finding was real and distinct from anything fixed above: **R4
names only `render_html` and `build_actions_script` for deletion, but
`_agent_chip`, `_spawn_nodes_html`, `_spawn_tree_html`, and
`_session_timeline_html` become orphaned dead code once `render_html`
goes** — each is called only from within `render_html`'s own body
(transitively; confirmed by tracing `_session_timeline_html`'s two call
sites, both inside `render_html`'s line range in both `.claude` and
`antigravity` trees), and `_spawn_tree_html`'s docstring cites the deleted
`fleet/reference.md`. Fixed: R4 now names all four helpers for deletion,
with a new AC (`grep -n "_agent_chip\|_spawn_nodes_html\|_spawn_tree_html\|
_session_timeline_html" .claude/skills/workboard/workboard.py` → no
matches), and the antigravity mirror AC extended to cover the same four
names. The embedded chip-CSS block (previously flagged) needed no separate
action — it's inside `render_html`'s own returned string, deleted
automatically. Confirmed non-vacuous in both trees today (10 matches on
the `.claude` leg). Re-run `/critique` to confirm READY.

## Re-critique 2026-07-14 (attended, /critique) — R4's 4-item fix was itself incomplete

The four-item enumeration verified accurate as far as it went, but a
fresh critic pass found it named a fraction of the real orphan set — the
same fragile-enumeration mistake this file has already hit twice
(finding 1's "10, not 2" antigravity count; this file's own note that a
hardcoded list goes stale). Independently verified via AST call-graph
reachability from the surviving entry points ({main, assemble,
attention_items, ready_items, default_roots} minus the render_html/
build_actions_script edges): **27 functions** are orphaned, not 4 —
including `render_batons`, `render_ready`, `render_actions`,
`render_inbox`, `render_filter_tiles`, `render_spend_section`, and 21
more, each confirmed to have its only call site(s) inside `render_html`'s
body. Fixed: R4 rewritten to state the reachability RULE rather than an
enumerated list (a hardcoded list will drift again as the file changes),
with the current 27-name set kept as illustrative, explicitly marked
"not exhaustive at implementation time." The fragile grep AC replaced
with a runnable AST-based reachability check (stdlib `ast` only, no new
dependency) that computes the same analysis mechanically — count-
independent and self-verifying against whatever the file looks like when
the task actually runs, rather than a name list that needs re-deriving
every round. Same check applies to the antigravity mirror since
workboard.py is confirmed byte-identical across both trees
(docs/memory/workboard-mirror-verbatim.md). Re-run `/critique` to
confirm READY.

## Re-critique 2026-07-14 (attended, /critique) — the reachability script itself was broken

The 27-name list and the reachability logic were confirmed exactly
right. But the embedded Python script had an `IndentationError` and
couldn't run at all — the AC it defined was unpassable regardless of
implementation correctness. Root cause: the script was nested inside a
markdown list item's own fenced code block, and this repo's
prose-formatter hook reflows list-item content, corrupting the
Python indentation in the process (same failure class as this session's
other spec-edit "Gotchas," documented in the resume-handoff's own
gotcha list). Fixed: moved the script to a new top-level `##
Reachability check script` section (not nested in any list), which
survives the formatter untouched — verified by extracting the exact
text from the committed file and running it, twice: once directly and
once via the AC's own copy-paste instructions. Also added the critic's
secondary point as explicit guidance: the check reports "clean" both
before AND after correct deletion (pre-deletion, everything is still
reachable through the not-yet-deleted `render_html`) — a worker must not
mistake a pre-deletion `clean` for "nothing to delete." Re-run
`/critique` to confirm READY.

## Re-critique 2026-07-14 (attended, resumed from handoff) — R4's function-only rule missed orphaned module-level constants

The 27-function reachability check itself was confirmed correct as far as
it went, but it walks only `ast.FunctionDef` nodes, so it cannot see
**module-level constants** orphaned by deleting `render_html` — chiefly
`TEMPLATE` (`workboard.py:2577-2827`, 251 lines, the HTML template
string; only consumer is `TEMPLATE.format(...)` inside `render_html`),
plus `STATE_BADGE`, `_NO_UNBLOCK_CHIP`, `_AGENT_CHIP_GLYPH`,
`INBOX_CATEGORIES`, `FILTER_CATEGORIES`, `_MODEL_DATE_RE` — each
confirmed today to have its only referencing code inside a function that
is itself in the deleted set (`badge`, `_unblock_marker`, `_agent_chip`,
`render_inbox`, `render_filter_tiles`, `_short_model_name`, all already
named in the 27-item list). R4 also made an affirmatively FALSE claim
that "the embedded chip-CSS block inside `render_html`'s own returned
string goes automatically with the function" — the chip CSS is actually
inside the module-level `TEMPLATE` constant, not inside `render_html`'s
body (which only does `return TEMPLATE.format(...)`). Both trees are
byte-identical (docs/memory/workboard-mirror-verbatim.md), so
antigravity has the same gap.

Fixed, addressing the recurring "the mechanical gate doesn't see X"
failure mode structurally rather than patching R4's prose a third time
(this is the second time a hardcoded/narrow enumeration under-covered the
real orphan set — see the two entries above): rewrote the reachability
script to walk general `Name`-Load references instead of only `Call`
edges, and to treat top-level simple `NAME = <expr>` assignments as
`defs` alongside functions — so one graph and one traversal now catches
both orphaned functions and orphaned module-level constants, with no
separate enumeration to keep in sync. Sanity-tested with a synthetic
before/after/incomplete-deletion fixture: a function-only version would
pass an incomplete deletion that leaves an orphaned constant behind (only
the function gone); the extended version correctly flags it
(`ORPHANED: ['CONST']`). Re-ran the exact script extracted from the
committed SPEC.md against both the `.claude` and `antigravity` copies of
`workboard.py` today — both print `clean` pre-deletion, matching the
documented pre-deletion-is-clean behavior. R4 rewritten to name the
constants explicitly (illustrative, not exhaustive, same caveat as the
function list) and to correct the false chip-CSS claim. New AC added:
`grep -n "^TEMPLATE = " workboard.py` → no match, as a concrete backstop
for the single largest orphaned item, alongside the now-dual-purpose
reachability-check AC. Re-run `/critique` to confirm READY.
