# Cross-repo rollout audit — 2026-07-22 pivot

The 2026-07-22 pivot (`specs/agentic-core-redesign/SPEC.md` addendum;
`specs/beads-daily-skill`) changes two things other repos on this
machine may need reconciled:

1. **Plugin distribution.** This repo ships as the `agentic` plugin
   (`.claude-plugin/plugin.json`, currently `0.12.0`) from the
   `agentic-toolkit` marketplace. Verified, not assumed: the
   `plugin-autorefresh` **Stop** hook and `plugin-staleness`
   session-start warn both live in `~/claude` and act on the
   **machine-global** plugin cache — no consuming repo carries its own
   copy of the hook, and no consuming repo pins an `agentic` version.
   So the version currency dimension has **no per-repo gap**: once the
   cache refreshes (a `~/claude` session's Stop hook after a version
   bump lands on origin, or the login-time update stack), every repo on
   the machine sees the new version. No repo needs a version action.
2. **Work-tracking reversal.** `docs/decisions/work-tracking.md`'s
   2026-07-03 "full exit" told every repo to drop bd for markdown
   `docs/TASKS.md`. This repo now reverses that **for itself only**
   (`specs/beads-daily-skill`). Other repos were never told to revert;
   each needs its own repo-local install decision. This audit finds the
   repos still echoing the full-exit and files a per-repo `decide`
   blocker for each — it does **not** edit any other repo's tree.

The bd re-adoption path for any repo recommended below is
`specs/beads-daily-skill/SPEC.md`'s "Installation in other repos"
steps (per-repo: `bd init` curated, `/gate` with the bd-compliance
check, `Bash(bd *)` allowlist, seed the queue).

## Per-repo classification

Candidates: every non-archived row in `~/REPOS.md` (11 rows; `~/archive/*`
is already retired). Classification per Step 2: (a) references
beads/`bd` in a way that predates or contradicts the pivot, or has no
bd mention despite being a real candidate; (b) plugin version currency;
(c) no action.

| Repo | Tracking state | Class | Stale phrase / gap (quoted) | Recommended action | Attended edit? |
| --- | --- | --- | --- | --- | --- |
| `~/claude` | Re-adopts bd (`specs/beads-daily-skill`) | (c) | — (source repo; plugin `0.12.0`, current) | None — this repo is the pivot's source | No |
| `~/automation` | `docs/TASKS.md`, no bd (std ✓, active) | (a) | `CLAUDE.md:14` "Task tracking: \`docs/TASKS.md\` (larger work: a spec under \`specs/\`)" | Per-repo decision: adopt bd via the extended `/onboard` install, or keep markdown deliberately | **Yes** |
| `~/budget_analysis` | No bd, minimal CLAUDE (20 lines) | (c) | — (small analysis repo, not a drain/agentic candidate) | None | No |
| `~/fooszone` | **Contradictory**: CLAUDE says markdown + decommissioned, AGENTS mandates bd | (a) | `CLAUDE.md:13` "tracker decommissioned 2026-07" vs `AGENTS.md:47` "Use \`bd\` for ALL task tracking—do NOT use TodoWrite, TaskCreate, or markdown TODO lists" | Reconcile the two files onto one tracker (decide bd or markdown, then edit both) | **Yes** |
| `~/hub` | No bd, active app (AGENTS ✗, 143-line CLAUDE) | (c) | — (never adopted bd; optional future adoption, not pivot-driven) | None (optional bd adoption is separate from this pivot) | No |
| `~/interview-prep` | `docs/TASKS.md`, bd decommissioned | (a) | `AGENTS.md:41` "Issue tracker (beads)—**decommissioned 2026-07**—task tracking is \`docs/TASKS.md\`" | Per-repo decision: adopt bd, or keep markdown deliberately | **Yes** |
| `~/portfolio-tracker` | `docs/TASKS.md`, bd decommissioned | (a) | `CLAUDE.md:172` "Historical issue archive at \`docs/beads-archive.jsonl\` (tracker decommissioned 2026-07)" | Per-repo decision: adopt bd, or keep markdown deliberately | **Yes** |
| `~/specs` | No bd, aggregation repo (33-line CLAUDE) | (c) | — | None | No |
| `~/vaults/life` | Obsidian vault, not a code repo | (c) | — | None | No |
| `~/ynab-mcp-new` (ynab-mcp-server) | `docs/TASKS.md` | (a) | `CLAUDE.md:183` "Small work: track as checkboxes in \`docs/TASKS.md\`" | **Covered by `specs/beads-daily-skill` CUJ-5 (bd issue `agentic-m22`)** — a live bd install run on this exact repo. Cross-referenced here; no new blocker filed (Step 5). | No (covered) |
| `~ (dotfiles, bare)` | Global `AGENTS.md` references `bd create` | (c) | `AGENTS.md:16` "create a task in Beads (\`bd create ...\`)" — consistent with the pivot's re-adoption direction | None — already bd-consistent | No |

## Summary

- **4 repos marked "attended edit needed"** (each gets one `HUMAN.md`
  `decide` blocker): `~/automation`, `~/fooszone`, `~/interview-prep`,
  `~/portfolio-tracker`.
- **1 repo cross-referenced** to existing work: `~/ynab-mcp-new` →
  `specs/beads-daily-skill` CUJ-5 (`agentic-m22`).
- **Plugin version:** no per-repo action anywhere — the machine-global
  plugin cache auto-refreshes; no repo pins a version.
- **This task wrote nothing outside `~/claude`.** The per-repo edits are
  the maintainer's call, filed as `HUMAN.md` blockers so they are not
  lost.
