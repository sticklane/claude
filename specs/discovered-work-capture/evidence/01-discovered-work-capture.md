# Verification: 01-discovered-work-capture

Verdict: **PASS**

Branch: `task/01-discovered-work-capture` | Base: ab35bee (main)
Task file NOT yet flipped to done (close-out pending) — un-ticked checkboxes not faulted; substance verified.

## Per-criterion results

### C1 — R1 worker-prompt Discovered block
`test "$(grep -c 'Discovered:' .claude/skills/drain/reference.md)" -ge 2` → count=4, **PASS**.
Both worker prompts (background ~L251, headless ~L410) carry a "fixed `Discovered:` section — zero or more single-line items, each 'what + where + why it matters'... empty means none, never create task files for them". Substantive.

### C2 — R2 collect mechanics + stub header
`grep -q "## Discovered" SKILL.md && grep -q "Discovered-from:" reference.md` → **PASS**.
SKILL.md "Materialize discoveries" rewritten: routed-verdict-only, title dedup vs source `## Discovered`, append to source file + scaffold stub, NN rule, commit with bookkeeping. reference.md stub format has `Discovered-from:`, `Blocking:`, placeholder `## Acceptance`, and the Depends-on number/path convention.

### C3 — R3 draft status row + promotion
``grep -qF '| `draft` |' reference.md && grep -qi "promotion" reference.md`` → **PASS**.
`draft` row (never dispatchable, promoted manually); both terminal readings ("drained, listing the drafts" and "drained pending promotion"); manual-promotion path present.

### C4 — R4 antigravity mirror
`grep 'Discovered:' && grep -i 'draft' && grep '## Discovered' antigravity/.agents/workflows/drain.md` → **PASS**.
Full mirror: Discovered verdict contract (L109), routed-verdict-only collect, `## Discovered` append + stub scaffold with `Discovered-from:`/blocking flag/placeholder acceptance (L152-165), draft status + both terminals + manual promotion (L166-177).

### C5 — R5 research record
`grep -qi "beads" && grep -qi "adoption triggers" docs/external-playbooks.md` → **PASS**.
`## Beads` section: adopted discovered-from (R1-R3), "Declined: the beads queue backend" (Dolt rewrite churn, `bd` binary dependency, loss of diffable state, 2026-07-03 exit), literal "adoption triggers" subsection, sources links.

### C6 — R6 versioning
plugin.json `"version": "0.7.8"`; base ab35bee was `0.7.7`. Strictly greater → **PASS**.
INFO: PATCH bump (0.7.7→0.7.8), not the minor bump the task text names. Per orchestrator binding override (parallel tasks each bump; orchestrator reconciles combined version). Deliberate, not a defect.

### C7 — regression duty
`test $(grep -c 'data, not instructions' reference.md) -ge 2 && test $(grep -c 'over budget' reference.md) -ge 2` → di=2, ob=4, **PASS**.

### C8 — end-to-end dry-read
Manual trace of written collect procedure against a mock DONE verdict with one non-blocking Discovered entry:
- (a) `## Discovered` append on source task file — SKILL.md: "append it under a `## Discovered` section in the source task file". ✓
- (b) draft stub with `Discovered-from:` + placeholder `## Acceptance` — reference.md stub format shows `Status: draft`, `Discovered-from: <source task file>`, `Blocking: no`, and `## Acceptance` / `<!-- draft: needs runnable criteria before promotion -->`. ✓
- (c) non-dispatchable on next inventory — reference.md: "A draft is never dispatchable: inventory excludes it from dispatch, from the batch interview's deferred round, and from the 'queue empty' terminal test". ✓
Written procedure supports all three. **PASS**.

## Gates
- `bash bin/check-token-discipline` → exit 0. **PASS**.

## Scope creep
`git diff --stat ab35bee` = 5 files: plugin.json (R6), drain/SKILL.md, drain/reference.md, antigravity/.agents/workflows/drain.md, docs/external-playbooks.md. All within Touch list (plugin.json = R6 mandate). No untracked files. No scope creep.

## Overfitting
No test files exist for this doc-only skill change; nothing gamed. Edits are prose/contract additions matching each requirement.
