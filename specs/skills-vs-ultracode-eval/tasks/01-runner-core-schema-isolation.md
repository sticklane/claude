# Task 01: Runner core — results schema, dry-run planner, config-dump arm isolation

Status: done
Depends on: none
Priority: P0
Budget: 24 turns
Rigor: prototype
Spec: ../SPEC.md (design statements 1-2, 6-8; acceptance criteria 1-2)
Touch: evals/headtohead/run.sh, evals/headtohead/result.schema.json, evals/headtohead/tasks.manifest, evals/headtohead/lib/

## Goal

The `evals/headtohead/` harness exists with `result.schema.json` (the per-run
JSONL row contract) and `run.sh` supporting `--dry-run` and
`--dry-run --dump-config`. Dry-run enumerates all 18 planned sessions
(2 arms × 3 tasks × 3 seeds) with full command lines and launches nothing.
The config dump proves arm isolation on paper: arm U has no plugin/skills mount
and carries the ultracode opt-in keyword in its brief; arm S mounts the plugin
and carries no keyword; both pin identical CLI version and plugin commit; and
every hidden `assert.sh` path plus every committed reference-solution path
resolves OUTSIDE both arms' mounts. This task builds the planning/config/isolation
core only — it never runs a session (task 02 does).

## Touch

Owns `run.sh` (creates it), `result.schema.json`, a task manifest naming the
three real tasks (`ledger`, `notes-api`, `sitegen`) plus the self-test tasks
(`fixture`, `crashfixture`), and any `lib/` helpers. Do NOT author the fixture
repos, reference solutions, the session-run path, or the judge path — those are
tasks 02-07. The path-outside-mount check must operate on the harness's PATH
LAYOUT (mount roots vs assert/reference path roots computed from the manifest),
so it passes without any fixture content existing yet; it will naturally also
cover the real fixtures once 04-06 land.

## Steps

1. Create `evals/headtohead/result.schema.json`: a JSON Schema for one results
   row with at least `task`, `arm`, `seed`, `pass` (bool), `usd`, `tokens`,
   `turns`, `wall_s`, `spawn_count`, `diff_lines`, `judge_score`. Mark the cost
   fields nullable-but-present (a crashed run records partial cost, never a
   dropped field).
2. Create `evals/headtohead/tasks.manifest` (or equivalent) listing task names
   and, per task, the in-mount snapshot path and the out-of-mount `assert.sh`
   and reference-solution paths. This is the single source the planner and the
   isolation check read.
3. Write `run.sh --dry-run`: emit exactly 18 lines/blocks (2 arms × 3 real
   tasks × 3 seeds) each showing the full command line that WOULD run; exit 0;
   launch nothing.
4. Write `run.sh --dry-run --dump-config`: print each arm's effective config and
   assert, in-script, (a) arm U: no plugin/skills mount, ultracode keyword
   present in brief; (b) arm S: plugin mount present, ultracode keyword absent;
   (c) both arms pin identical CLI version and plugin commit; (d) for every task
   in the manifest, its `assert.sh` path and reference-solution path resolve
   outside BOTH arms' mount roots. Print each assertion's result as evidence and
   exit non-zero if any fails.
5. Mechanical acceptance run (prototype rigor: acceptance-command run replaces
   red-first) — confirm each command below behaves as specified.

## Acceptance

- [x] `bash evals/headtohead/run.sh --dry-run` → prints 18 planned sessions with full command lines, exits 0, launches nothing — verified: prints `[1/18]`..`[18/18]` (3 real tasks × 2 arms × 3 seeds), exit 0.
- [x] `bash evals/headtohead/run.sh --dry-run --dump-config` → prints arm U with no plugin/skills mount and the ultracode keyword in its brief; arm S with the plugin mount and no ultracode keyword; both pinning identical CLI version and plugin commit; and every `assert.sh` and reference-solution path resolving OUTSIDE both arms' mounts; exits 0 — verified: all 16 in-script assertions print `PASS`, exit 0.
- [x] `python3 -m json.tool evals/headtohead/result.schema.json >/dev/null` → exits 0 (schema is valid JSON) — verified exit 0.
