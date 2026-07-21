# Task 01: agentic-register tells subsection + mirror + gate + version

Status: done
Depends on: none
Priority: P1
Budget: 12 turns
Spec: ../SPEC.md (requirements R1, R2, R5, R6)
Touch: .claude/skills/prose-review/reference.md, antigravity/.agents/skills/prose-review/reference.md, tests/mirror-procedure-manifest.txt, .claude-plugin/plugin.json

## Goal

`.claude/skills/prose-review/reference.md` carries a new `## Agentic-register
tells` subsection (after the nine-item rubric): three runtime-neutral tells —
T1 meta-discourse (announce-then-do narration), T2 false precision on knowable
quantities, T3 evaluative varnish substituting for the checkable fact — each
with a cited source, a before→after rewrite, and a one-line boundary against
the nearest rubric item, plus a status-telegraphy carve-out modeled on the
item-1 carve-out. The subsection is mirrored verbatim-equivalent into the
Antigravity copy, seeded in the parity manifest so the coverage gate enforces
it, the reference TOC block names it, and `plugin.json` version is bumped to
0.9.30. Codex inherits via its existing symlink (no Codex edit here).

## Touch

Edit only the four listed paths. Do NOT touch CLAUDE.md, antigravity/AGENTS.md,
or codex/AGENTS.md — those author-side edits are task 02, which cites the
subsection this task finalizes. The authored prose must itself avoid the tells
it documents (no meta-discourse, no varnish) — dogfood the doctrine.

## Steps

1. Add the `## Agentic-register tells` subsection to reference.md after the
   nine-item rubric (before or after the Diátaxis section). State it applies
   to any RLHF-trained assistant; carry no operator-specific raw counts (if a
   count is cited, label it "measured on one operator's Claude corpus,
   illustrative"). For each tell write: name, one-line description, ≥1 cited
   source (arXiv id from the spec's Research grounding), a `Before:` / `After:`
   rewrite, and its boundary line (T1 vs item 6; T2 vs item 2; T3 vs items 5
   and 9).
2. Add the status-telegraphy carve-out to the subsection: name the item-1
   carve-out as its model; draw the boundary (a line that STATES verifiable
   state like `gates green` is exempt; a bare adjective SUBSTITUTING for that
   state like `landed clean` is a T3 hit); give one exempt example and one
   T3-hit example; carry the "when unsure, do not flag" guard.
3. Update the reference.md Table of contents block to name the new subsection.
4. Mirror the subsection into
   `antigravity/.agents/skills/prose-review/reference.md` — content-coverage
   equivalent (all three tell names + the carve-out present), not a byte diff
   (this mirror is a paraphrased port). Ensure any citation path is
   runtime-neutral or antigravity-valid, never a `.claude/` path.
5. Add a real (non-comment) `<source>|<mirror>|<phrase>` data line to
   `tests/mirror-procedure-manifest.txt`:
   `.claude/skills/prose-review/reference.md|antigravity/.agents/skills/prose-review/reference.md|Agentic-register tells`
6. Bump `.claude-plugin/plugin.json` `version` from 0.9.29 to `0.9.30`.
7. Run the coverage gate and the acceptance commands below.

## Acceptance

- [x] `grep -q '^## Agentic-register tells' .claude/skills/prose-review/reference.md` → present — grep -c returned 1
- [x] `test $(awk '...' | grep -Eio 'meta-discourse|false precision on knowable|evaluative varnish' | sort -u | wc -l) -eq 3` → three distinct tell names — extracted names: evaluative varnish / false precision on knowable / meta-discourse
- [x] each tell cited + has a before→after — grep -Eic 'arxiv|liang|kobak|singhal|kalai' = 8 (≥3); grep -c 'Before' = 3 (≥3)
- [x] runtime-neutral, no operator counts — 'RLHF-trained assistant' present (2 lines); '717,369|519 (local )?sessions' absent (0 matches)
- [x] status-telegraphy carve-out block — 'status-telegraphy carve-out'=1, 'item-1'=1, 'gates green'=1, T3-hit 'landed clean'=2 all present
- [x] TOC block names it — awk-extracted TOC block matches 'agentic-register' (1)
- [x] real manifest data line — `grep -Eq '^[^#].*\|Agentic-register tells' tests/mirror-procedure-manifest.txt` matched (1)
- [x] `bash tests/test_mirror_procedure_coverage.sh` → exits 0 — gate_exit=0
- [x] mirror carries the full subsection — antigravity subsection extracted names: evaluative varnish / false precision on knowable / meta-discourse (3 distinct)
- [x] `grep -q '^## Agentic-register tells' codex/.agents/skills/prose-review/reference.md` → Codex symlink resolves — grep -c returned 1 (symlink → antigravity mirror)
- [x] version bumped from its base value — `git show HEAD:.claude-plugin/plugin.json` = "0.9.29"; working tree = "0.9.30"
- [x] `test $(wc -l < .claude/skills/prose-review/SKILL.md) -lt 500` → SKILL.md untouched, 84 lines
