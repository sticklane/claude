# Runtime profile: claude-code

The default profile. It reproduces the toolkit's behavior exactly as it
ships today — a repo with no `.claude/runtime.md` (see
[README.md](README.md)) runs this profile unchanged.

## Tiers

| Tier          | Model                                                      | Notes                                                                |
| ------------- | ---------------------------------------------------------- | -------------------------------------------------------------------- |
| scout-tier    | Haiku (`haiku`) at `effort: low`                           | Cheap, fast, read-only reconnaissance — the `scout` agent's default. |
| session-tier  | inherit                                                    | The conversation's own model; whatever the session runs.             |
| deep-tier     | Opus 4.8 (`claude-opus-4-8`; Agent-tool short name `opus`) | Recommended pin value — opt-in, not an active default.               |
| frontier-tier | Fable (`claude-fable-5`; Agent-tool short name `fable`)    | Recommended pin value — opt-in, not an active default.               |

The two deep-tier rows are recommended pin values, not active defaults:
dispatchers route deep-tier/frontier-tier work to these models only when
a repo's `.claude/runtime.md` pins the tier explicitly (the selection
and override convention lives in [README.md](README.md)). With no pin,
deep and frontier work inherits the session model — today's behavior,
zero new cost.

## Role pins

Adopted routing defaults (spec: model-routing-native-config, C1–C3).
Routing lives only in `.claude/settings.json` and agent/skill
frontmatter — never in prompt prose; `bin/check-agent-model-pins`
enforces the agent pins. Aliases only, never dated model ids, so pins
survive model releases. The other profiles carry the same table in
their runtime's vocabulary.

| Role                                                                 | Claude default                                                                                                                 |
| -------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------ |
| session default                                                      | `opusplan` (`.claude/settings.json`) — Opus reasoning in plan mode, Sonnet execution                                           |
| implementation workers (drain dispatch, incl. group throughput mode) | `opus` — deep-tier adopted default; the alias always resolves to the current Opus release, never a dated snapshot              |
| explore / codebase-search (`scout`)                                  | `haiku`                                                                                                                        |
| verifier (acceptance evidence; advisory reviewer lane)               | `sonnet`                                                                                                                       |
| `critic` (spec/plan/diff critique)                                   | `opus` — deep-tier per token-discipline ("architecture critique"); a critic pass costs ~1% of a wrong implementation           |
| `/distill` (skill frontmatter)                                       | `opus`                                                                                                                         |
| retry escalation (attempt 2, verifier evidence in prompt)            | `fable` — a retry after a deep-tier (`opus`) attempt failed, the frontier-tier sanction in `.claude/rules/token-discipline.md` |
| tournament escalation (attempts 3+, after the `fable` retry failed)  | `fable` — same frontier-tier alias as the retry above, now run as 3 concurrent angle-variant attempts instead of 1             |

Frontier stays sparing beyond that one active rung: security-critical
review and novel-architecture sessions are the other two sanctioned
frontier uses (token-discipline.md), and both remain **manual** — `/model
fable` for the session, or an explicit frontier-tier pin in
`.claude/runtime.md` for a `critic` dispatch — never a heuristic
auto-escalation (docs/decisions/orchestration.md).

## Headless

Today's non-interactive contract, as used by the drain and autopilot
headless fallbacks (`.claude/skills/drain/reference.md` is the
authoritative copy; this template restates its contract without
changing it):

```bash
claude -p "<prompt>" \
  --allowedTools "<allowlist>" \
  --permission-mode dontAsk --max-turns <turn cap> \
  --model <tier alias>
```

- `<prompt>` — a self-contained single-agent prompt (no skill
  references, no subagent fan-out; the allowlist has no Task tool, so
  scout/verifier calls would abort under `dontAsk`).
- `<allowlist>` — e.g. `"Read,Edit,Write,Glob,Grep,Bash(<verified
test/lint/build cmds>),Bash(git add *),Bash(git commit *)"`.
- `<turn cap>` — the task's `Budget:` turn count when present, else 80;
  the hard cap behind the prompt's soft stop.
- `<tier alias>` — the Role pins ladder, same rungs as Task-tool
  dispatch: `opus` attempt 1, `fable` relaunch, `fable` tournament.

`dontAsk` makes unapproved tools abort instead of hanging — the CI
baseline from the playbook's mechanism ladder.

This is drain's **canonical worker allowlist** — the tool-complete
`<allowlist>` default for compute-heavy specs, one named template, defined
here once, that drain's Headless fallback references by name instead of
restating an allowlist ad hoc. It covers the common toolchains (`go`,
`bash`, `npm`, `python3`) plus `git` scoped to `add`/`commit` (never push —
the worker prompt forbids it):

```
"Read,Edit,Write,Glob,Grep,Bash(go *),Bash(bash *),Bash(npm *),Bash(python3 *),Bash(git add *),Bash(git commit *)"
```

The drain reference's allowlist pre-flight still widens this per the pending
tasks' acceptance commands — a spec whose tests invoke a tool outside the
default gets it added before dispatch.

## Orchestration

- **Primitive**: the Workflow tool (multi-agent orchestration in the
  harness).
- **Invocation surface**: named deterministic scripts in
  `.claude/workflows/`, fired only on the explicit human "ultracode"
  opt-in (docs/human-gates.md, reason 5 — orchestration scripts are
  human-gated so injected text can never launch a fleet).
- **Structured output**: schema-validated returns from workflow steps.
- **Resume**: journaled — an interrupted run resumes from its journal
  with cached-prefix replay rather than restarting.
- **Parallelism cap**: per-run concurrency cap set on the workflow run.

## Orchestration (ultra)

> **Model-agnostic cross-reference (sanctioned fourth section).**
> `specs/model-agnostic/SPEC.md` R1 fixes the runtime-profile minimum at
> three sections — `## Tiers` / `## Headless` / `## Notes`. This
> `## Orchestration (ultra)` block is a deliberate _superset_, not drift: a
> later model-agnostic edit must NOT "normalize" it away. (The preceding
> `## Orchestration` block states the deterministic Workflow-tool facts;
> this one carries the opt-in gate, effort tiers, resume rules, and the
> per-variant script templates.)

Ultra mode is the Workflow-tool orchestration path shared by `/critique`,
`/drain`, `/build`, and `/idea`. It is **off by default** and
fires only when BOTH conditions hold:

1. **the ultracode opt-in is active.** The opt-in rules belong to the
   Workflow tool's own tool description; restated here, the opt-in forms are
   the **`ultracode` keyword**, a **session flag**, or the **user's own
   explicit ask**. No opt-in → the skills run their non-ultra path verbatim.
2. **the active runtime profile documents this section** — i.e. this
   `runtimes/claude-code.md` is present in the checkout. Plugin installs and
   eval fixtures ship without `runtimes/`, so the gate reads permanently
   closed there and the skills behave exactly as today.

Both are required; the ~10–15× token multiple of a fanned-out run is never
spent on an auto-trigger. Ultra is for breadth-first or verification-critical
work only.

### Effort tiers (dispatch-prompt language)

Every ultra dispatch prompt carries Anthropic's proven anti-runaway scaling
rule (prompted tiers, not a hard cap):

- simple lookup → **1 agent / 3–10 tool calls**
- direct comparison → **2–4 agents / 10–15 tool calls each**
- **10+ agents only** for genuinely breadth-first work.

### Resume

Workflow runs are journaled. Resume an interrupted run with its
**`scriptPath`** plus **`resumeFromRunId`** (the run id returned by the
original dispatch). The durable checkpoint, though, is the **file
artifacts**, not the journal: a resumed run re-reads each task file's
**`Status:`** line before dispatching, so anything already committed (a
`Status: done` flip) is skipped and drain's "orchestration without an
orchestrator" invariant survives the interrupt. Losing the workflow run
loses nothing — re-running non-ultra drain picks up from the same committed
task-file state.

### Templates

<!--
  SCHEMA-CHECK DATE: 2026-07-03. The Workflow-tool API surfaced below —
  agent / parallel / pipeline / phase / log / budget, budget.remaining(),
  and scriptPath + resumeFromRunId (see Resume) — is the schema recorded on
  2026-07-03 (per specs/ultra-mode/SPEC.md R1). SDK/tool surfaces change
  quickly, so re-verify these names against the live Workflow tool schema
  before generating or running a script. Scripts are generated per run from
  these templates and are NOT committed (SPEC.md "Out of scope"); helper
  calls (topoGroups, dedupe, refutePrompt, …) are illustrative stand-ins.
-->

**Critique panel** (`/critique`) — 3–5 lens-diverse critics over one
artifact pointer, deduped, then adversarially verified (a finding dies on
majority refute):

```js
// critique-panel.js — Schema-check date: 2026-07-03.
const LENSES = [
  "correctness",
  "security",
  "verification-gaps",
  "scope",
  "cost-if-missed",
];
export default async function ({ agent, parallel, log, artifact }) {
  const raised = await parallel(
    LENSES.map((lens) =>
      agent({
        role: `critic:${lens}`,
        prompt: `Review ${artifact} through the ${lens} lens. 3–10 tool calls.`,
      }),
    ),
  );
  const deduped = dedupe(raised.flat());
  const votes = await parallel(
    deduped.map((f) => agent({ role: "verify-vote", prompt: refutePrompt(f) })),
  );
  const relayed = deduped.filter((_, i) => votes[i].majority !== "refute");
  log({
    phase: "critique-panel",
    raised: deduped.length,
    relayed: relayed.length,
  });
  return relayed;
}
```

**Drain dispatch** (`/drain`, sequential queue and group throughput mode
alike) — dependency graph
compiled from the task files' `Depends on:` headers into a pipeline over
groups (barrier only between groups), one worker per task, a verifier per
task, and the status-flip + commit after each verdict exactly as non-ultra
drain does:

```js
// drain-dispatch.js — Schema-check date: 2026-07-03.
export default async function ({
  pipeline,
  parallel,
  agent,
  phase,
  budget,
  tasks,
}) {
  // Baton boundary: the MAIN session treats this long workflow as its own
  // baton boundary — the run's `scriptPath` + `resumeFromRunId` (see Resume)
  // plus each task's committed `Status:` line make the main session
  // disposable, so a heavy/compacted main hands off and resumes the run
  // here instead of grinding. Points at drain's baton mechanism
  // (.claude/skills/drain/SKILL.md §3a "Baton pass"); don't duplicate the grammar.
  const groups = topoGroups(tasks); // from `Depends on:` headers, not ## Parallelization prose
  await pipeline(
    groups.map((group) => async () => {
      await parallel(
        group.map((task) => async () => {
          if (budget.target && budget.remaining() <= 0)
            return phase("budget-stop", task);
          const result = await agent({ role: "worker", worktree: true, task }); // today's prompt + effort tiers
          const verdict = await agent({ role: "verifier", task, result });
          await commitStatusFlip(task, verdict); // writes `Status: done|blocked`, then commits
        }),
      );
    }),
  );
}
```

**Verification votes** (`/build`) — acceptance commands run first as the
deterministic gate; criteria with no runnable command get a 3-verifier
refute-majority vote; the fix/re-verify loop is bounded at 4 cycles, then
flips to blocked with the failure evidence:

```js
// build-verify.js — Schema-check date: 2026-07-03.
export default async function ({ agent, parallel, run, task }) {
  for (let cycle = 1; cycle <= 4; cycle++) {
    const cmd = await Promise.all(task.acceptanceCommands.map(run)); // deterministic gate first
    const votes = await parallel(
      task.judgedCriteria.map((c) =>
        agent({ role: "verify-vote", lens: c.lens, prompt: refutePrompt(c) }),
      ),
    );
    if (cmd.every(ok) && majorityPass(votes)) return "done";
    await agent({ role: "worker", task, prompt: "fix the failing criteria" });
  }
  return "blocked"; // bounded at 4 cycles
}
```

**Idea fan-out** (`/idea`) — a multi-modal scout sweep plus a completeness
critic before the interview, used only when the gate is open and the idea
spans multiple repos or subsystems:

```js
// idea-scout.js — Schema-check date: 2026-07-03.
const MODES = ["by-structure", "by-convention", "by-history", "by-dependency"];
export default async function ({ parallel, agent, idea }) {
  const surveys = await parallel(
    MODES.map((mode) =>
      agent({
        role: `scout:${mode}`,
        prompt: `${mode} sweep for ${idea}. 3–10 tool calls.`,
      }),
    ),
  );
  const gaps = await agent({
    role: "completeness-critic",
    prompt: gapPrompt(surveys),
  });
  return { surveys, gaps }; // replaces the 2–4 ad-hoc scouts of the non-ultra path
}
```

## Notes

- **Config locations**: project — `.claude/settings.json` (shared) and
  `.claude/settings.local.json` (per-machine), `CLAUDE.md`,
  `.claude/skills/`, `.claude/agents/`, `.claude/rules/`; user-global —
  `~/.claude/settings.json`, `~/.claude/CLAUDE.md`.
- **Permission modes**: `default` (prompt per tool), `acceptEdits`
  (auto-approve file edits), `plan` (read-only), `dontAsk` (unapproved
  tools abort — the headless/CI mode above), `bypassPermissions`
  (approve everything; sandboxed use only).
- **Runtime selection / tier overrides**: `.claude/runtime.md`,
  documented once in [README.md](README.md).
