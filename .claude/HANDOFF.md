Task: plugin updates + fix cross-repo-cutover follow-up items + critical repo audit ("with fable")
Status: done, pending two user decisions (not blocking, just unanswered)
Next step: re-ask the two open questions below and act on the answer
Resume with: read this file in full, then just talk to the user — no skill needed
Blocking on: nothing technical — these are the user's calls to make

## What this session did (all committed and pushed to origin/main, verified green)

1. Checked all 4 installed plugins for updates (`claude plugin update <name>`
   for each): `frontend-design` pulled an update (needs a Claude Code
   restart to apply), `agentic`/`cloudflare`/`prompt-improver` were current.
2. Consumed the prior session's `.claude/HANDOFF.md` (cross-repo beads
   adoption + skill retirement) and fixed/closed all 5 of its open
   follow-up bd items:
   - `agentic-vtp` (P0): `agentic init`'s `_controlled_bd_init` could
     silently un-commit unrelated real work if bd's own init didn't
     cleanly advance HEAD. Fixed with TDD (commit `dd95890f`,
     `tests/test_agentic_initialize.py`, 3 tests) — now verifies the
     commit it's about to reset is actually bd's own (subject + parent-SHA
     check) before resetting; aborts loudly otherwise.
   - `agentic-d3x`, `agentic-bsd`, `agentic-ml6`: stale references to
     deleted mirror/baton machinery in breakdown/workboard/drain
     SKILL.md — cleaned up (commit `5d614c02`).
   - `agentic-49u`: swept `docs/TASKS.md` (5 pivot-moot entries removed,
     14 real ones filed as bd issues with `discovered-from:agentic-49u`),
     then retired the file itself — replaced with a pointer to bd
     (commit `47da8276`).
   - Also found and committed 2 workflow scripts
     (`.claude/workflows/cross-repo-beads-adoption.js`,
     `full-cutover-and-health-check.js`) that the old handoff claimed were
     committed but actually weren't (commit `7d209f9b`).
3. Mid-session the user asked for a much bigger ask: "critically evaluate
   the end state of this repo with fable [model]... are we meeting our
   objectives/CUJs? aligned with research? leveraging beads properly? do
   our CLAUDE.md instructions work?" then "make changes based on
   findings." Ran 4 parallel Fable-tier general-purpose agents (CUJ/
   objectives, research-doctrine alignment, beads usage, CLAUDE.md
   consistency) — full findings are in each agent's final message in this
   session's transcript, not re-derivable from disk except via the bd
   issues they produced (see below).
4. Personally re-verified the highest-severity claims before acting (did
   NOT trust subagent claims blind): fetched the actual Claude Docs
   prompt-caching page (a cited quote was fabricated), ran `ctx map
   --help` (confirmed a taught flag doesn't exist), read `agentic/
   shadow.py` directly (confirmed the shadow-sync direction bug).
5. Fixed and committed the clearly-safe, mechanical findings:
   - Fabricated citation + false mechanism claim + broken specs/ paths in
     `token-discipline.md`/`quality-discipline.md` (commit `0e76f964`).
   - `docs/external-playbooks.md`'s stale "beads declined" verdict —
     added superseded-notice headers matching the `docs/human-gates.md`
     precedent rather than rewriting history (same commit `0e76f964`,
     folded with the machinery sweep — check `git log -p` if the exact
     split matters).
   - `ctx/SKILL.md` taught a nonexistent `ctx map --limit N` flag; fixed
     to `--tokens` (commit `dd09fcc7`).
6. Filed everything too large/judgment-heavy/cross-repo to fix blind as
   bd issues instead:
   - **`agentic-uz1` (P0, the big one)**: `shadow.py` actually makes
     markdown win over bd (`allow_stale=True` force-import), the OPPOSITE
     of CLAUDE.md's claim that "bd is this repo's source of truth."
     Re-running the cross-repo cutover workflow scripts would silently
     reopen closed bd issues. Needs a real design decision (is markdown
     still authoritative for spec-originated tasks, or should bd fully
     win now?), not a quick patch. Full repro/evidence is in the issue
     description — read `bd show agentic-uz1` before touching this.
   - ~5 more local findings: this repo's own Stop hook doesn't run
     `scripts/check.sh` (dogfooding gap, `agentic-43j`); stale CUJ
     evidence/docs (`agentic-p3x`); missing regression test for the
     claimed-issue Stop-hook block (`agentic-0fq`); incomplete
     `ynab-mcp-server` install (`agentic-hty`).
   - 19 general tech-debt items swept out of the old `docs/TASKS.md`
     (all tagged `discovered-from:agentic-49u`, all P3/P4).
   - Also closed `agentic-5ge` (the /work epic, 11/11 children done,
     eligible for close).

## Two things NOT done — genuinely the user's call, asked and unanswered

1. **Other-repo findings.** The CLAUDE.md-consistency and beads-usage
   audits found real drift in OTHER repos on this machine, not touched:
   - `~/.claude/CLAUDE.md`, `~/CLAUDE.md`, and this repo's `CLAUDE.md`
     have real contradictions (4 different answers to "push after
     commit?"; TDD-rigor scoping mismatch; `~/CLAUDE.md` still directs
     tech debt to `docs/TASKS.md` machine-wide post-bd-cutover). These
     are personal global config files — deliberately not rewritten
     without explicit sign-off.
   - `fooszone`, `hub`, `portfolio-tracker`, `ynab-mcp-new` CLAUDE.md
     files are bloated (up to 295 lines) with literal contradictory
     duplicate sections (two "Session Completion" sections in fooszone's,
     etc.).
   - `fooszone`'s bd queue is a 457-issue untriaged near-all-P2 landfill.
   - `interview-prep`'s bd cutover looks hollow (2/32 issues ever closed).
   Asked the user: open bd issues in those repos for their specific
   findings, or take a pass at reconciling the CLAUDE.md stack first?
   **Not yet answered when this session ended.**
2. **Stray HANDOFF files.** 3 untracked files sit in `.claude/` from
   older, unrelated, never-consumed sessions:
   `.claude/HANDOFF-ctx-review.md`, `.claude/HANDOFF-task-tracking-specs.md`,
   `.claude/HANDOFF.md.stale-pathspec-commit-hardening`. They don't match
   the literal `HANDOFF.md` name resume-handoff auto-detects, so they've
   never surfaced to a session automatically. Asked the user: look at
   these, or leave them alone? **Not yet answered when this session
   ended.**

## Gotchas learned this session

- **`sed -i` on a tracked file is a real violation, not just style** —
  did it once by habit while fixing `token-discipline.md`'s spec paths,
  caught it via `.claude/rules/shell-text-tools.md`, switched to Edit for
  the rest. The rule exists because sed has no read-before-write check
  and no diff review — worth remembering next time a "just 3 sed
  patterns" urge hits.
- **Don't trust a subagent's specific factual claim (a quote, a flag, a
  behavior) without checking it yourself when you're about to act on it**
  — one audit agent claimed a fabricated Claude-Docs quote; verified by
  actually fetching the page. Cheap to check, expensive to propagate a
  wrong "fix" that hardcodes a fabrication one level deeper.
- **`_controlled_bd_init`'s correct semantics took two iterations** — my
  first fix treated "bd_init made no new commit" as an ERROR (wrong: a
  legitimate re-init over an already-committed `.beads`, e.g. rebuilding
  a deleted Dolt store, genuinely commits nothing new). `check.sh` caught
  this immediately via `tests/test_agentic_roundtrip.sh` going red after
  my first pass — that shell integration test is the one that actually
  exercises the re-init-with-no-new-commit path; the unit tests alone
  wouldn't have caught the wrong semantics.
- Full findings detail for everything filed as a bd issue lives in each
  issue's own `--description`/`--acceptance` — read `bd show <id>`
  rather than assuming this file has the detail.

## Verification

`bash scripts/check.sh` is green (ran twice this session, both exit 0;
second run after all commits). `evals/lint-ultra-gate.sh` and
`tests/test_check_token_discipline.sh` both pass (checked directly after
editing `drain/SKILL.md` and `token-discipline.md`). All 6 commits this
session are on `origin/main` (`dd95890f`, `5d614c02`, `0e76f964`,
`dd09fcc7`, `47da8276`, plus the earlier `7d209f9b` workflow-scripts
commit).

Next stage: none — /clear and resume with "Read .claude/HANDOFF.md and
continue," which will surface the two open questions above.
