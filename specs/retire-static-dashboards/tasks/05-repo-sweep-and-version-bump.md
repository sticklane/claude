# Task 05: Repo-wide fleet reference sweep, dangling-citation cleanup, version bump

Status: done
Depends on: 01, 02, 03, 04
Priority: P1
Budget: 7 turns
Spec: ../SPEC.md (requirements R1, R7, plus the whole-repo AC and evals check)
Touch: .claude-plugin/plugin.json, .claude-plugin/marketplace.json, AGENTS.md, docs/agent-dashboards.md, docs/external-playbooks.md, .claude/skills/drain/SKILL.md, .claude/skills/workboard/SKILL.md, .claude/skills/_shared/viz.py

## Goal

Every reference to `/fleet` outside the four files Tasks 01/02 already
rewrote is updated to describe fleet's new inline-table output instead of
an HTML snapshot, EXCEPT legitimate unrelated prose uses of the word
"fleet" (generic idioms like "scale the fleet", "a fleet of launched
[workers]") and antigravity's own exempted mentions (Task 04 leaves those
untouched). Every dangling citation of the deleted `fleet/reference.md`
path is gone. `.claude-plugin/plugin.json`'s version is bumped.

## Touch

Exactly the files listed above (re-verify each hit by content, not by the
spec's line-number snapshots). Do not touch antigravity (Task 04 already
did its leg) or any file Tasks 01-03 already own.

## Steps

1. Inventory every `/fleet`/"fleet" mention via
   `git grep -n '\bfleet\b' -- .claude/ antigravity/ docs/ AGENTS.md CLAUDE.md .claude-plugin/`
   and classify each: update-to-inline-table, dangling-reference.md-citation
   (already fixed by Tasks 01/02/04's function deletions or needing a
   direct edit here), or legitimate-unrelated-prose (leave alone).
2. Update at minimum: `.claude-plugin/plugin.json`'s description ("a
   `/fleet` dashboard of open agents"), `.claude-plugin/marketplace.json`
   ("the /fleet open-agents dashboard"), `AGENTS.md` ("workboard/fleet
   views"), `docs/agent-dashboards.md` ("the session-scoped `/fleet`"),
   `docs/external-playbooks.md` ("`/fleet` covers the live view"),
   `.claude/skills/drain/SKILL.md`'s "/fleet shows the workers live"
   mention, `.claude/skills/workboard/SKILL.md`'s "For agents in THIS
   session only, use /fleet instead" line, and
   `.claude/skills/_shared/viz.py`'s docstring claiming "`/workboard`,
   agent-console, and `/fleet` render the same way" (reword — false once
   fleet prints a plain table) plus any comment pointing at the deleted
   `fleet/reference.md`.
3. Leave unchanged: any generic "scale the fleet"/"a fleet of launched
   [workers]" idiom, and `antigravity/README.md:35`'s not-ported row
   (correct as-is, not stale).
4. Bump `.claude-plugin/plugin.json`'s `version`.
5. Confirm no eval fixture points at fleet's old output:
   `git grep -ln 'fleet\.html\|--out\|--emit-fleet-css' -- evals/` should
   return no matches.
6. Run `bash evals/lint-ultra-gate.sh` (this task's `drain/SKILL.md` edit
   touches an ultra-path skill).
7. Record the manual-pending item as evidence: running `/fleet` in a
   session with at least one background agent must print the markdown
   table and summary line directly, writing no file anywhere — this
   requires an attended session with a live harness `TaskList`, which a
   drained/unattended worker cannot exercise. Note this explicitly rather
   than silently skipping it.

## Acceptance

- [x] `git grep -n '\bfleet\b' -- .claude/ antigravity/ docs/ AGENTS.md CLAUDE.md .claude-plugin/`
      shows only: the new inline-table description, legitimate unrelated
      prose, or `antigravity/README.md:35`'s not-ported row — no stale
      HTML-snapshot description and no dangling `fleet/reference.md`
      citation anywhere else.
      Evidence: 30 hits reviewed; 8 Touch files reworded to inline-table wording (plugin.json/marketplace.json/AGENTS.md/viz.py/drain+workboard SKILL.md/agent-dashboards.md/external-playbooks.md), rest are idioms, fleet's own updated skill, valid status-vocab refs, or antigravity README:35 — verifier PASS.
- [x] `git grep -rn 'fleet/reference\.md' -- .claude/ antigravity/` returns
      no matches.
      Evidence: exit 1, no output — viz.py:35 reworded to "the fleet skill"; verifier PASS.
- [x] `.claude-plugin/plugin.json`'s version is higher than its value at
      this task's own base commit (`git show <base-commit>:.claude-plugin/plugin.json | grep version`
      compared against the current value, not a hard-coded prior literal).
      Evidence: base 0b654ac = 0.9.11, current = 0.9.12; verifier PASS.
- [x] `git grep -ln 'fleet\.html\|--out\|--emit-fleet-css' -- evals/`
      returns no matches.
      Evidence: exit 1, no output; verifier PASS.
- [x] `bash evals/lint-ultra-gate.sh` exits 0.
      Evidence: "lint-ultra-gate: OK — all ultra mentions gated in 4 files", exit 0; verifier PASS.
- [ ] **Manual-pending**: running `/fleet` in a session with at least one
      background agent prints the markdown table and summary line
      directly, writing no file — recorded as evidence, not an automated
      check (docs/memory/unattended-worker-tool-limits.md); the
      orchestrator or a human runs it post-merge.
      MANUAL-PENDING (not run): an unattended worker cannot exercise a live
      harness TaskList with a background agent; left unticked for the
      orchestrator/human to run `/fleet` post-merge and confirm it prints
      the markdown table + summary line inline, writing no file.
