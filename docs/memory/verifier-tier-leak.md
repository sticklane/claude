# Verifier tier leak — stale plugin cache served `model: inherit`

**Read when:** an agent's frontmatter `model:` pin (verifier=sonnet,
scout=haiku, etc.) appears not to hold in a cost profile — a pinned agent
billed at the session's frontier model — or when reasoning about why a
shipped agent-def fix doesn't show up in a running install.

## What happened

agentprof (window 2026-07-04→11, spec `agent-tier-leaks` R1) showed the
`verifier` agent running part of its spend on `claude-fable-5` despite
`.claude/agents/verifier.md` pinning `model: sonnet`. Regenerating the
samples (`agentprof claude --since 2026-07-04T00:00:00Z`) and filtering for
verifier stack frames at `claude-fable-5` found ~$117 of fable-model verifier
calls across 13 sessions, splitting two ways:

- **Plugin-served frames** (`agent:agentic:verifier`, ~$84). Sessions
  `5dcdc5c4`, `b5cd2c76`, `7e277508`, `ee0f4482` — their transcripts under
  `~/.claude/projects/` reference the plugin path
  `cache/agentic-toolkit/agentic/0.6.2/`. The **0.6.2 cache snapshot pins
  `model: inherit`**, so the verifier inherited the session model. Those
  sessions ran main-line on `claude-fable-5` (5dcdc5c4: 527 fable main-line
  msgs; b5cd2c76: 189), so `inherit → fable`. The 5 verifier dispatches in
  5dcdc5c4 carried **no explicit `model` override** — the leak is the pin,
  not the dispatch site.
- **Repo-local frames** (`agent:verifier`, bare, ~$33). Sessions `cd09d9e5`,
  `61ec4803` ran 2026-07-03, before the sonnet pin commit (below), and show
  no plugin-cache path — served by a `verifier.md` still on `model: inherit`
  at that time. (Which `.claude/agents/` dir served the bare frames is the
  `agent-tier-leaks` R3 namespace question — resolved separately.)

Confirmed outcome: this is the pre-pin `model: inherit` leak, not an
overriding dispatch path or a deliberate escalation.

## Version boundary

- The repo added `model: sonnet` to `verifier.md` in commit `01062e9`
  ("feat(routing): … role pins …"), **plugin version 0.7.15**, 2026-07-04
  18:34 UTC. Every earlier version, back to the initial commit, carried
  `model: inherit`.
- But the *installed* cache never held a 0.7.x snapshot after 0.7.0. Snapshots
  present: `0.6.2` (inherit), `0.7.0` (inherit), `0.8.3` / `0.8.7` / `0.8.13`
  (all sonnet). So from the running install's perspective the observable
  boundary is **`inherit` ≤ 0.7.0 → `sonnet` ≥ 0.8.3** — which is why the spec
  hypothesized 0.8.3 even though the repo fix shipped at 0.7.15.

## The immutable-cache mechanism

Installed plugins are served from immutable, per-version snapshots under
`~/.claude/plugins/cache/agentic-toolkit/agentic/<version>/`, never from the
dev checkout. A snapshot is frozen at the version it was cut from, and a
running session dispatches agents from whatever snapshot the install currently
points at. So a fix landed in the repo (sonnet pin at 0.7.15) does **not** take
effect for a user until the installed plugin is updated to a version whose
snapshot carries it (here, 0.8.3+). Until then the old snapshot keeps serving
its old pin — `inherit` — and a frontier-model (fable) session leaks pinned
agents to frontier rates. The cache snapshots are immutable: the fix is a
forward version bump + `claude plugin update`, never an edit to a cached
snapshot.

## Check

```sh
# What does each installed snapshot pin?
for d in ~/.claude/plugins/cache/agentic-toolkit/agentic/*/; do
  printf '%s -> ' "$(basename "$d")"
  grep -m1 '^model:' "$d/.claude/agents/verifier.md"
done
# Re-trace fable-model verifier spend (regen samples; --days 7 has moved on):
#   agentprof claude --since 2026-07-04T00:00:00Z -o /tmp/leak-samples.jsonl
#   then filter stacks with agent[:agentic]:verifier + claude-fable-5.
# A leak session's plugin version is in its transcript:
#   grep -oE 'cache/agentic-toolkit/agentic/[0-9.]+' ~/.claude/projects/<enc-cwd>/<session>.jsonl
```

If a profile shows a pinned agent on the wrong model, first check the
installed snapshot's pin (above), not just the repo file — the repo can be
correct while the running install is a stale snapshot.
