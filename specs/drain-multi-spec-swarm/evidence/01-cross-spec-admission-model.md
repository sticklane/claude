# Verification evidence: Task 01 cross-spec-admission-model

Verdict: PASS

## Per-criterion results

| #   | Command                                                                                | Result                                        |
| --- | -------------------------------------------------------------------------------------- | --------------------------------------------- |
| 1   | `grep -c "At most one dispatch lease is held at a time" .claude/skills/drain/SKILL.md` | 0 (grep exit 1, no match) ✓                   |
| 2   | `grep -ci "swarm" .claude/skills/drain/SKILL.md .claude/skills/drain/reference.md`     | SKILL.md:4, reference.md:2 → combined 6 ≥ 3 ✓ |
| 3   | `grep -c "up to 3 simultaneously-held spec leases" .claude/skills/drain/reference.md`  | 1 ≥ 1 ✓                                       |
| 4   | `grep -c "≤10\|<= 10\|10 total" .claude/skills/drain/reference.md`                     | 2 ≥ 1 ✓                                       |
| 5   | `wc -l < .claude/skills/drain/SKILL.md`                                                | 500 ≤ 500 ✓                                   |
| 6   | `grep -A5 -i "already-green" reference.md \| grep -ci "spec-review.md"`                | 1 ≥ 1 ✓                                       |
| 7   | `grep -ci "single global serial merge queue\|one single global" reference.md`          | 1 ≥ 1 ✓                                       |
| 8   | `grep -c "in-flight tasks from that task's OWN spec" reference.md`                     | 1 ≥ 1 ✓                                       |
| 9   | `grep -c '"Window empty" means zero live' reference.md`                                | 0 (exit 1) ✓                                  |
| 10  | `grep -c "with every in-flight task — two tasks may run together" reference.md`        | 0 (exit 1) ✓                                  |
| 11  | `grep -c "fires independent of the per-spec" reference.md`                             | 1 ≥ 1 ✓                                       |
| 12  | `grep -c "Hard cap: W ≤ 5.*on TOTAL" SKILL.md`                                         | 0 (exit 1) ✓                                  |
| 13  | `grep -c "on TOTAL" reference.md`                                                      | 0 (exit 1) ✓                                  |
| 14  | `grep -c "W ≤ 5" SKILL.md reference.md`                                                | SKILL.md:1, reference.md:1 → combined 2 ≥ 1 ✓ |
| 15  | `grep -ci "shared global window\|one shared global\|shared pool" reference.md`         | 2 ≥ 1 ✓                                       |
| 16  | `git diff --name-only <base>..HEAD \| grep -c breakdown-paths`                         | 0 ✓ (no breakdown files touched)              |
| 17  | `bash evals/lint-skill-size-gate.sh`                                                   | "lint-skill-size-gate: OK" exit 0 ✓           |
| 18  | Full merge-time gate suite                                                             | all exit 0 (see below) ✓                      |

### Full gate suite (criterion 18/19)

- `bash evals/lint-skill-size-gate.sh` → exit 0
- `bash specs/status.sh` → exit 0 (draft:7 in-progress:1 obsolete:9 pending:11 all:151)
- `claude plugin validate .` → exit 0, "✔ Validation passed"
- `./bin/check-agent-model-pins` → exit 0
- `bash evals/lint-ultra-gate.sh` → exit 0, "OK — all ultra mentions gated in 4 files"
- `for f in tests/test_*.sh; do bash "$f"; done` → all 16 test files exit 0
  (test_antigravity_content_parity, test_antigravity_parity,
  test_check_token_discipline, test_codex_parity,
  test_deep_research_synthesis_guard, test_doc_links,
  test_drain_owner_protocol, test_drain_scheduler_window,
  test_hook_templates, test_install_docs, test_install_gates,
  test_mirror_procedure_coverage, test_plugin_version_helper,
  test_review_skip, test_screen_stub, test_sync_workflows)

## Append-only task-file check

`git diff 95a7bd13cb80356cbec1ca86f3e86770cc9c9d3c..HEAD -- 'specs/drain-multi-spec-swarm/tasks/*.md'`
against committed HEAD shows no diff (task file's Status/PLAN edits are still
uncommitted working-tree changes, not yet part of HEAD). Diffing against the
working tree (`git diff <base> -- ...`) shows only:

- `Status: pending` → `Status: in-progress`
- Insertion of the `<!-- PLAN ... -->` comment block

No edits to Goal/Steps/Touch/Budget/Acceptance-criterion text. Constraint
satisfied.

## Coherence sanity read

- SKILL.md line 34-35 names the reference.md section as "Cross-spec
  admission & merge (R1–R12)"; reference.md line 1648 header is
  `## Cross-spec admission & merge (R1–R12)` — same title, confirmed match.
- The two removed unqualified sentences (`"Window empty" means zero live...`
  and `...with every in-flight task — two tasks may run together`) are gone
  (greps 9/10 both 0) and replaced in place with spec-scoped versions (line
  1690-1694 "own window is empty... OWN spec"; line 1696-1703 new
  cross-spec-co-admissibility paragraph).
- Two-level cap is stated without contradiction: SKILL.md line 145
  "**Per-spec cap: W ≤ 5** bounds a single claimed spec's own live workers
  (unchanged); in swarm mode all claimed specs share **one global pool
  capped at ≤10 total**"; reference.md lines 1705-1713 restate the same
  split (per-spec W≤5 survives, cross-spec sum throttled to ≤10, not the
  naive per-spec sum). No self-contradiction found.

## Scope-creep check

Touch list restricted to `.claude/skills/drain/SKILL.md` and
`.claude/skills/drain/reference.md`. `git diff <base>..HEAD --stat` confirms
only these two files (plus the task file's own working-tree-only edits) are
touched; no `breakdown` mirror files, `token-discipline.md`, or
`.claude-plugin/plugin.json` changes present (criterion 16 confirms 0
breakdown-path hits).

## Gates

All of: `evals/lint-skill-size-gate.sh`, `specs/status.sh`,
`claude plugin validate .`, all `tests/test_*.sh` (16 files),
`./bin/check-agent-model-pins`, `evals/lint-ultra-gate.sh` — exit 0.

## Verdict

PASS — all 18 acceptance bullets exercised and green; append-only
constraint holds; edited-region coherence confirmed; no scope creep found.
