# Review fixes: branch code-review findings

## Problem

The branch code review verified 16 findings across the toolkit: a plugin
manifest that fails `claude plugin validate`, gaps and dead states in
/drain's state machine, an inconsistent task-header contract, worker
prompts that reference an uninvokable plugin skill, a gate Stop hook that
would block workers' contractual mid-red stops, a fragile evals runner,
missing distribution caveats and unconditional evidence-commit assumptions,
and stale antigravity/docs mirrors. All findings are verified; fixes are
prescribed per cluster in the task files.

## Requirements

One task per cluster; the task files under `tasks/` carry the prescribed
fixes in full.

- Cluster 01 — plugin manifest: `agents` as array of .md paths,
  marketplace description, CLAUDE.md caveat. No version bump (99 owns it).
- Cluster 02 — drain state machine: headless done-flip, BLOCKED-over-budget
  routing after merge-failure relaunch, stale failed-row, merge-conflict
  `git merge --abort` before branch discard. Antigravity mirror.
- Cluster 03 — header contract: `Touch:` becomes a header line in the
  breakdown template; drain inventory reads all four headers (adds Budget);
  plan-comment blocks sit below header lines. Antigravity mirrors.
- Cluster 04 — worker prompt resolution: dispatchers resolve build's
  SKILL.md to a concrete path at dispatch (kill the dead plugin branch);
  Budget forwarding to autopilot/parallel workers; `Budget: <N> turns`
  integer format pinned. Antigravity mirrors.
- Cluster 05 — gate collision: verdict-line bypass contract in gate's Stop
  hook (DEFERRED/BLOCKED/INCOMPLETE are sanctioned stops); interaction
  noted in autopilot/drain references. Antigravity gate mirror.
- Cluster 06 — evals runner robustness: nullglob, unknown-skill guard, git
  config isolation, cleanup trap, keep-fixture-on-FAIL with per-scenario
  log, scout tool grants in the scenario allowlist.
- Cluster 07 — evals distribution + evidence: toolkit-repo-only caveat;
  build's evidence commit conditional on a passed evidence path; drain's
  evidence assertions scoped to specs/<slug>/ layouts. Antigravity mirrors.
- Cluster 08 — mirrors and docs: antigravity evals assert.sh provisioning,
  antigravity build unattended path + verdict, external-playbooks ranking
  sentence, README Option C rules copy, drain-tournament SPEC portable grep.
- Cluster 99 — version bump + sweep: one minor bump for the whole batch,
  full acceptance re-run across all queues, stale version-pin note. Global
  terminal task.

## Out of scope

- The feature specs in sibling dirs — `specs/chaining-antipatterns/`, `specs/code-vs-llm/`,
  `specs/context-management/`, `specs/model-agnostic/` — own their features
  and versioning clauses; nothing here implements or edits them.

## Acceptance criteria

- [ ] Cluster 01: `claude plugin validate .` → exit 0
- [ ] Cluster 02: `test "$(grep -c 'git merge --abort' .claude/skills/drain/SKILL.md)" -ge 2 && ! grep -rq "either prior attempt" .claude/skills/drain antigravity/.agents/workflows/drain.md && ! grep -q "two failed attempts" .claude/skills/drain/reference.md` → exit 0
- [ ] Cluster 03: `grep -q "^Touch:" .claude/skills/breakdown/SKILL.md && grep -q "Budget" .claude/skills/drain/SKILL.md && grep -q "below the header lines" .claude/skills/build/SKILL.md` → exit 0
- [ ] Cluster 04: `! grep -rq "plugin's skills\|plugin's build skill" .claude/skills/drain/reference.md .claude/skills/parallel/SKILL.md .claude/skills/autopilot/reference.md && grep -q "over budget" .claude/skills/parallel/SKILL.md && grep -q "over budget" .claude/skills/autopilot/reference.md && grep -q "Budget: <N> turns" .claude/skills/breakdown/SKILL.md` → exit 0
- [ ] Cluster 05: `grep -q "sanctioned stop" .claude/skills/gate/reference.md && grep -q "sanctioned stop" antigravity/.agents/skills/gate/reference.md` → exit 0
- [ ] Cluster 06: `bash -n evals/run.sh && grep -q "shopt -s nullglob" evals/run.sh && grep -q "GIT_CONFIG_GLOBAL=/dev/null" evals/run.sh && grep -q "unknown skill" evals/run.sh` → exit 0
- [ ] Cluster 07: `grep -q "toolkit repo" .claude/skills/evals/SKILL.md && grep -q "inline in the task file" .claude/skills/build/SKILL.md && grep -q "specs/<slug>/ layout" .claude/skills/drain/SKILL.md` → exit 0
- [ ] Cluster 08: `grep -q "drain ranks the survivors mechanically" docs/external-playbooks.md && grep -q "unless launched unattended" antigravity/.agents/workflows/build.md && ! grep -qF '\-t1\|t1' specs/drain-tournament/SPEC.md` → exit 0
- [ ] Cluster 99: `python3 -c "import json; assert json.load(open('.claude-plugin/plugin.json'))['version']=='0.7.0'"` → exit 0, plus every task's Acceptance re-run green across all queues (pin synced 0.4.0→0.7.0 to the combined-bump target — intervening rf-02/rf-07 bumps advanced the baseline to 0.6.2; see tasks/99 + evidence/99)

## Open questions

(none)

## Parallelization

See [specs/QUEUE.md](../QUEUE.md) — the combined-queue wave plan is
kept in one copy there; this spec's tasks and their `Depends on:`
headers carry the machine-readable graph.
