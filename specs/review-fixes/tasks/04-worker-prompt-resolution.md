# Task 04: Worker prompts — resolve build skill path at dispatch, forward Budget, pin format

Status: done
Depends on: 03
Budget: 40 turns
Spec: ../SPEC.md (cluster 04)

## Goal

Worker prompts tell agents to "invoke /agentic:build or read build's
SKILL.md from the plugin's skills directory" — a dead branch, since agents
cannot invoke `disable-model-invocation` skills and don't know the plugin
install path. Dispatchers (drain step 2, parallel step 2, autopilot)
instead resolve build's SKILL.md to a concrete path at dispatch time and
substitute it into the worker prompt. Also: autopilot's prompt template
and parallel's worker prompt gain the over-budget BLOCKED stop (drain
already has it), breakdown pins the Budget format to `Budget: <N> turns`
(integer N), and drain's headless `--max-turns` extraction cites that
format. (Depends on task 03: both edit breakdown's template block and the
drain files.)

## Touch

- `.claude/skills/drain/reference.md` (both worker prompts, ~line 53;
  headless `--max-turns` extraction)
- `.claude/skills/parallel/SKILL.md` (worker prompt, ~line 34)
- `.claude/skills/autopilot/SKILL.md` and
  `.claude/skills/autopilot/reference.md` (prompt template, ~lines 59-61)
- `.claude/skills/breakdown/SKILL.md` (Budget line format)
- `antigravity/.agents/workflows/drain.md`,
  `antigravity/.agents/workflows/parallel.md`,
  `antigravity/.agents/workflows/autopilot.md`,
  `antigravity/.agents/skills/breakdown/SKILL.md` (mirrors)

## Steps

1. In each dispatcher (drain step 2 / reference worker prompts, parallel
   step 2, autopilot's prompt template), add a dispatch-time step: resolve
   build's SKILL.md to a concrete path (in-repo
   `.claude/skills/build/SKILL.md`, or the plugin cache path found at
   dispatch) and substitute it into the worker prompt, e.g. "follow the
   procedure in <resolved path>, resolved at dispatch". Delete the
   "invoke /agentic:build or read from the plugin's skills directory"
   branch — agents cannot invoke disable-model-invocation skills.
2. Add the over-budget BLOCKED stop (same wording as drain's worker
   prompts: stop with verdict BLOCKED "over budget" when remaining work
   clearly exceeds the budget) to autopilot's prompt template and
   parallel's worker prompt.
3. In breakdown's template, pin the Budget header to `Budget: <N> turns`
   (integer N — no ranges, no prose) so dispatchers can parse it; update
   the template's example line accordingly.
4. In drain reference's headless fallback, make the `--max-turns`
   extraction cite the pinned `Budget: <N> turns` format as its source.
5. Mirror 1-3 into the antigravity drain/parallel/autopilot workflows and
   breakdown skill.

## Acceptance

- [x] `! grep -rq "plugin's skills\|plugin's build skill" .claude/skills/drain/reference.md .claude/skills/parallel/SKILL.md .claude/skills/autopilot/SKILL.md .claude/skills/autopilot/reference.md` → exit 0 (dead branch gone) — verified exit 0, see ../evidence/04-worker-prompt-resolution.md (C1)
- [x] `grep -q "resolved at dispatch" .claude/skills/drain/reference.md && grep -q "resolved at dispatch" .claude/skills/parallel/SKILL.md && grep -qr "resolved at dispatch" .claude/skills/autopilot/` → exit 0 (concrete-path substitution instruction present) — verified exit 0, see ../evidence/04-worker-prompt-resolution.md (C2)
- [x] `grep -q "over budget" .claude/skills/parallel/SKILL.md && grep -qr "over budget" .claude/skills/autopilot/` → exit 0 (Budget stop forwarded) — verified exit 0, see ../evidence/04-worker-prompt-resolution.md (C3)
- [x] `grep -q "Budget: <N> turns" .claude/skills/breakdown/SKILL.md` → exit 0 (integer format pinned) — verified exit 0, see ../evidence/04-worker-prompt-resolution.md (C4)
- [x] `grep -q "<N> turns" .claude/skills/drain/reference.md` → exit 0 (headless --max-turns cites the pinned format) — verified exit 0, see ../evidence/04-worker-prompt-resolution.md (C5)
- [x] `grep -q "resolved at dispatch" antigravity/.agents/workflows/drain.md && grep -q "over budget" antigravity/.agents/workflows/parallel.md && grep -q "over budget" antigravity/.agents/workflows/autopilot.md && grep -q "Budget: <N> turns" antigravity/.agents/skills/breakdown/SKILL.md` → exit 0 (mirrors) — verified exit 0, see ../evidence/04-worker-prompt-resolution.md (C6)
