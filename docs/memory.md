# Memory index

Narrow, load-on-demand lessons. Read the topic file when a task matches its
trigger; this index is not loaded at session start. One line per topic:
path — when to read.

- [worktree-base-tracking-ref](memory/worktree-base-tracking-ref.md) — worktree agents see stale files / miss merged deps / conflict on merge (cut from `origin/main`, not HEAD).
- [unattended-worker-tool-limits](memory/unattended-worker-tool-limits.md) — authoring a drainable task, a worker DEFERRED because it "couldn't run" a criterion (no Workflow tool / no `disable-model-invocation` skills), or smoke-testing a gated skill (an Agent dispatch can't actually invoke `/build`/`/drain`/`/autopilot`/`/evals` — hard-blocked even on explicit human-directed instruction).
- [live-drain-reconciliation](memory/live-drain-reconciliation.md) — asked to reconcile in-progress tasks or clear stale/needs-review/unpushed git flags: check for a LIVE drain first (task/\* worktrees, advancing `drain:` commits, Status flipping) — it owns that cleanup; manual edits collide.
- [workboard-mirror-verbatim](memory/workboard-mirror-verbatim.md) — editing the workboard skill (workboard.py / test_workboard.py), or writing `/breakdown` acceptance criteria for a task touching `antigravity/` mirrors: only workboard's `.py` files are byte-identical (port with `cp` + `diff -q`); prose-skill mirrors are paraphrased ports — never write a `diff → no output` criterion for those.
- [concurrent-session-collision](memory/concurrent-session-collision.md) — starting a multi-file edit, or files change under you that you didn't edit: check no OTHER live Claude session shares the (non-worktree) tree (`ps aux | grep 'claude daemon'`) before proceeding; on collision stop and don't revert load-bearing changes.
- [skill-retirement-checklist](memory/skill-retirement-checklist.md) — retiring/folding/renaming a skill or workflow: what a clean reference grep still misses (bare-name mentions, unported behaviors, fallback paths, host-invariant clashes) and why the critic runs on the diff anyway.
- [root-container-test-failures](memory/root-container-test-failures.md) — tests/test\_\*.sh failing in a root container (remote/web session): three known chmod-based failures are environmental; confirm on clean HEAD and report, don't fix.
- [drain-dispatch-lessons](memory/drain-dispatch-lessons.md) — dispatching drain/build workers when a gate is already red on main, a worker spawns its own verifier sub-agent, or a task's Touch lives in another repo (live-service checkout): the three prompt clauses / procedures that handle it.
- [touch-root-fixture-tests](memory/touch-root-fixture-tests.md) — authoring/reviewing a task that changes a parser's sample/fixture output: list the root-level `*_test.go` files asserting fixture sample counts (e.g. `agentprof/cmd_claude_test.go`) in `Touch:`, or the worker is forced outside its declared scope to keep the suite green.
