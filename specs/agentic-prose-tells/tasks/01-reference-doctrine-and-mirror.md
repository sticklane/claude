# Task 01: agentic-register tells subsection + mirror + gate + version

Status: pending
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

- [ ] `grep -q '^## Agentic-register tells' .claude/skills/prose-review/reference.md` → present
- [ ] `test $(awk '/^## Agentic-register tells/{f=1;next} /^## /{f=0} f' .claude/skills/prose-review/reference.md | grep -Eio 'meta-discourse|false precision on knowable|evaluative varnish' | sort -u | wc -l) -eq 3` → three distinct tell names
- [ ] `SUB=$(awk '/^## Agentic-register tells/{f=1;next} /^## /{f=0} f' .claude/skills/prose-review/reference.md); test $(printf '%s' "$SUB" | grep -Eic 'arxiv|liang|kobak|singhal|kalai') -ge 3 && test $(printf '%s' "$SUB" | grep -c 'Before') -ge 3` → each tell cited + has a before→after
- [ ] `awk '/^## Agentic-register tells/{f=1;next} /^## /{f=0} f' .claude/skills/prose-review/reference.md | grep -qi 'RLHF-trained assistant'` and `! awk '/^## Agentic-register tells/{f=1;next} /^## /{f=0} f' .claude/skills/prose-review/reference.md | grep -Eq '717,369|519 (local )?sessions'` → runtime-neutral, no operator counts
- [ ] `awk '/^## Agentic-register tells/{f=1;next} /^## /{f=0} f' .claude/skills/prose-review/reference.md | grep -qi 'status-telegraphy carve-out'` and the block matches `item-1`, `gates green`, and a T3-hit example
- [ ] `awk '/## Table of contents/{f=1;next} f&&/^Loaded on demand/{f=0} f' .claude/skills/prose-review/reference.md | grep -qi 'agentic-register'` → TOC block names it
- [ ] `grep -Eq '^[^#].*\|Agentic-register tells' tests/mirror-procedure-manifest.txt` → real manifest data line
- [ ] `bash tests/test_mirror_procedure_coverage.sh` → exits 0
- [ ] `test $(awk '/^## Agentic-register tells/{f=1;next} /^## /{f=0} f' antigravity/.agents/skills/prose-review/reference.md | grep -Eio 'meta-discourse|false precision on knowable|evaluative varnish' | sort -u | wc -l) -eq 3` → mirror carries the full subsection
- [ ] `grep -q '^## Agentic-register tells' codex/.agents/skills/prose-review/reference.md` → Codex symlink resolves
- [ ] `git show HEAD:.claude-plugin/plugin.json | grep -q '"version": "0.9.29"' && grep -q '"version": "0.9.30"' .claude-plugin/plugin.json` → version bumped from its base value
- [ ] `test $(wc -l < .claude/skills/prose-review/SKILL.md) -lt 500` → SKILL.md untouched, under budget
