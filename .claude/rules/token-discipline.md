# Token discipline

Context is the scarce resource. Every token in the main conversation is
re-sent on every subsequent turn, so pollution compounds. Spend main-context
tokens on decisions; delegate consumption of raw material to subagents.

## Delegation defaults

- **Never read files into main context to "look around."** Use the `scout`
  agent (scout-tier, read-only; Claude default: Haiku) for any
  where/how/what-exists question. Fan out
  multiple scouts in parallel for independent questions; you keep the
  conclusions, not the file dumps.
- Read a file directly only when you are about to edit it, and prefer reading
  the relevant slice over the whole file.
- Verification, review, and research that produce lots of intermediate output
  belong in subagents (`verifier`, `critic`, `Explore`) whose transcripts are
  discarded — only their final report costs you anything.

## Model and effort matching

Four rungs, cheapest first — don't pay frontier-model rates to run `grep`:

- scout-tier → mechanical or lookup work (Claude default: Haiku at low
  effort; the `scout` default).
- session-tier → ordinary judgment work (specs, review, tricky
  implementation): the conversation's own model.
- deep-tier (Claude default: Opus 4.8) → heavy judgment above the session
  default: final review of a large diff, subtle-bug hunts, architecture
  critique.
- frontier-tier (Claude default: Fable) → ONLY work that truly needs the
  strongest model: novel architecture decisions, security-critical review,
  or a retry after a deep-tier attempt failed.

Skills that spawn agents — at their actual spawn points: drain's tournament
workers and per-candidate verifier runs, /design's candidate investigators,
an on-demand verifier escalation — consult `.claude/runtime.md` tier pins
and pass the mapped model through the harness's model parameter. No config,
or no pin for the tier in question → inherit the session model (the deep
tiers are opt-in: profile rows are recommended pin values, not active
defaults). Pins bind Agent-tool dispatch only; the headless fallback
templates run their profile's default in v1.

## Session hygiene

- One task per session — light artifact stages may self-chain per
  CLAUDE.md's conventions. When a task completes, `/clear` and start the
  next from its task file rather than carrying dead context forward.
- Long-running work should be resumable from artifacts on disk (specs, task
  files, notes in `docs/`), never from conversation memory. If a session is
  getting heavy mid-task, write a handoff file and restart from it.
- Don't re-run searches or re-read files already established this session;
  don't paste large command output back into the conversation — summarize it.

## Cache economics

- Prompts are cached static-first: stable content (rules, skill text,
  unchanged files) belongs at the front of prompts and must not churn
  mid-session.
- Editing CLAUDE.md or `.claude/rules/` mid-session invalidates the
  cached prefix for every later turn — batch such writes at session end
  (as /distill does).
- Tool-set changes bust caches: don't add/remove MCP servers or edit an
  agent's `tools:` list mid-run. Harness-managed deferred tool loading
  is exempt — it's designed for this.

## Cheap before expensive

- Critique the spec before implementing it (a `critic` pass costs ~1% of a
  wrong implementation).
- Make acceptance checks runnable commands, so verification is one cheap
  subagent instead of an interactive debugging spiral.
