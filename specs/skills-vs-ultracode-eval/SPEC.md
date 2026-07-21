# Head-to-head evaluation: this repo's skills vs ultracode, on Claude Code CLI

Breakdown-ready: false
Rigor: prototype
Status: waiting
Unblock: ask: Which 3 mid-sized coding tasks form the corpus? Candidates must meet the selection criteria in "The corpus" — name 3 repos/tasks or approve the suggested sourcing.

## The question

On the same mid-sized coding tasks, same model, same container: which
configuration finishes more tasks correctly, and at what cost —
Claude Code CLI with **ultracode orchestration and none of our skills**,
or Claude Code CLI with **our skills toolkit and no ultracode**?

This is the first direct measurement of whether the toolkit earns its
keep against the platform's own multi-agent mode. Either answer is
useful: a loss on cost or correctness tells us which parts to keep.

## The design in plain statements

1. Two arms. **Arm U**: bare Claude Code CLI, no plugin, no custom
   skills or rules; each task brief carries the documented ultracode
   opt-in keyword. **Arm S**: this repo's `agentic` plugin installed
   (skills, agents, rules); ultracode never opted in; no other
   difference.
2. Everything else pinned and identical: model ID, effort, container
   image, network policy, repo snapshot per task (a git ref), and the
   task brief text (identical except the arm-U opt-in keyword — each
   arm's mechanism is activated exactly the way its documentation says
   to activate it, and nothing else is added).
3. No arm-specific coaching. Arm S's brief does not name any skill;
   whether skills trigger is part of what is measured — a toolkit that
   only works when the human invokes it by name has an adoption
   problem, which is a finding, not noise.
4. The corpus is 3 mid-sized coding tasks (60–90 minutes at human
   scale, multi-file, in codebases with green test suites). Each task
   ships as: a repo snapshot ref, a ≤6-sentence brief, and a **hidden
   acceptance script** (held out of both arms' filesystems) that runs
   the repo's tests plus task-specific checks. Hidden because a
   visible script invites teaching-to-the-test in both arms.
5. Each arm runs each task **3 times** — 18 headless sessions total.
   Variance across the 3 seeds is reported alongside the mean; a
   configuration that passes 3/3 cheaply but occasionally is worse
   than one that passes 2/3 predictably, and the numbers must show
   that.
6. Measured per run, recorded as one JSONL row: hidden-script
   pass/fail (primary); total cost in USD and tokens from the session
   transcript; wall-clock; turn count; subagent/workflow spawn count;
   diff line count; and a single-call rubric-judge score (1–5,
   correctness-independent maintainability), with the judge blinded —
   its prompt contains the diff and brief, never the arm.
7. Verdict rule, fixed before any run: an arm wins a task on pass
   count first, median cost among passing runs second. Results are
   reported per task and in aggregate; no single blended scalar.
8. The runner extends the existing evals machinery
   (`evals/headtohead/run.sh` + per-task `setup.sh`/hidden
   `assert.sh`), and is launched only via `/evals` — paid headless
   sessions stay human-launched.
9. The first full run's results land in this spec's `EVIDENCE.md` as
   the finding; the harness, not the finding, is what the tasks below
   build.

## The corpus (selection criteria — the open decision)

A candidate task qualifies if: its repo has a green test suite at the
snapshot ref; the work spans ≥3 files; the brief fits in 6 sentences
with no hidden requirements; correctness is checkable by tests
(existing + task-specific hidden ones), not by reading prose; and the
repo fits the container (no privileged setup, no interactive auth —
docs/memory/unattended-worker-tool-limits.md). Suggested sourcing:
one task each from three real repos on this machine that already meet
the criteria (e.g. the ynab-mcp-server, budget_analysis, and
agent-console codebases), authored as fixture snapshots so runs are
repeatable. The maintainer names or approves the 3 (Unblock above);
everything else in this spec is decided.

## Controls and honesty rules

- Arm isolation is verified, not assumed: the runner dumps each
  session's effective config, and the dry-run asserts arm U mounts no
  plugin/skills directory and arm S carries no ultracode opt-in.
- The hidden acceptance script never enters either arm's filesystem
  or prompt; it runs post-session against the produced worktree.
- One results schema, validated per row; a run that crashes or hits
  the session cap records as fail with its partial cost — dropped
  runs would silently flatter the crashier arm.
- Caps: per-session turn cap and USD cap, identical across arms,
  recorded in the config dump.
- The judge never sees cost, wall-clock, or arm; correctness comes
  only from the hidden script.

## Acceptance criteria

For building the harness (the corpus decision gates running it, not
building it):

- [ ] `bash evals/headtohead/run.sh --dry-run` → lists 18 planned
      sessions (2 arms × 3 tasks × 3 seeds) with full command lines,
      and exits 0 without launching anything
- [ ] `bash evals/headtohead/run.sh --dry-run --dump-config` → arm U's
      config shows no plugin/skills mount and contains the ultracode
      keyword in its brief; arm S's shows the plugin mount and no
      ultracode keyword (asserted by the script, printed as evidence)
- [ ] `bash evals/headtohead/run.sh --task fixture --arm S --seeds 1`
      → completes end-to-end against a bundled toy fixture task and
      emits a results row that validates against
      `evals/headtohead/result.schema.json`
- [ ] `grep -ciE "arm|ultracode|skills" evals/headtohead/judge-prompt.md`
      → `0` (judge blinding)
- [ ] fixture run's results row contains non-null `usd`, `tokens`,
      `turns`, `wall_s` populated from the real transcript

Next stage: /critique specs/skills-vs-ultracode-eval/SPEC.md, then
/breakdown after the corpus Unblock is answered (human-launched).
