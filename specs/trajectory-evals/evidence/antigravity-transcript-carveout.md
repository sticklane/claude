# Antigravity transcript carve-out (trajectory-evals task 04)

Task 03 documented an opt-in v2 trajectory assertion for the Claude Code
eval runner: `assert.sh` may read `EVAL_TRANSCRIPT`, an environment
variable the runner sets to the absolute path of the run's JSONL
transcript, and grep the turn-by-turn events to grade _how_ a run behaved
(e.g. `grep -q '"subagent_type":"scout"' "$EVAL_TRANSCRIPT"`).

Task 04 (step 2) asks whether `antigravity/.agents/workflows/evals.md`
should receive the equivalent documentation — which requires Antigravity's
headless Agent Manager runs to produce a **locatable, machine-greppable
turn-by-turn transcript file** the way `claude -p --output-format
stream-json` does. They do not. This file records the check and why the
carve-out (documenting the absence rather than mirroring the feature) is
the correct outcome.

## What produces the transcript on Claude Code

`claude -p --output-format stream-json` emits a structured JSONL stream of
per-turn events — tool calls, subagent dispatches, messages — to a file
the runner can locate and hand to `assert.sh` via `EVAL_TRANSCRIPT`. A
trajectory assertion greps that JSONL for structured markers like
`"subagent_type":"scout"`. The whole mechanism depends on a stable,
structured, per-turn transcript existing on disk.

## What Antigravity's headless CLI actually exposes

Checked `runtimes/antigravity.md`, the Headless section, item
**Structured output** (the "no `--json`/`-o` flag in `agy --help`" bullet,
around lines 148-151), confirmed live against `antigravity-cli` 1.1.1:

- There is **no `--json` / `-o` / `--output-format` flag** on `agy -p` —
  no structured-output mode at all. This is the same gap the profile's
  Structured-output bullet records for the interactive surface.
- The response prints as **prose / markdown to stdout**, not as a
  turn-by-turn event stream. Prose stdout is not greppable for structured
  trajectory markers the way stream-json JSONL is.
- A run _sometimes_ points at a generated artifact file under
  `~/.gemini/antigravity-cli/brain/<uuid>/`. That is a single generated
  _output artifact_ the model chose to write, not a stable per-turn
  transcript of the run's trajectory: its presence is conditional ("sometimes"),
  its path is a per-run uuid the runner is not told, and its contents are
  whatever the model produced — there is no documented schema, no
  guarantee of subagent-dispatch events, and no way to locate it
  deterministically. It cannot back a `grep -q '"subagent_type":..."'`
  trajectory assertion.

## Why the carve-out is correct

From this repo alone, Antigravity's Agent Manager / `agy -p` runs expose
no locatable, structured, turn-by-turn transcript file that a v2
trajectory assertion could read. Mirroring the `EVAL_TRANSCRIPT`
documentation into `antigravity/.agents/workflows/evals.md` would assert a
capability the runtime does not have — a load-bearing procedural
divergence the mirror-procedure discipline forbids inventing. The honest
mirror records the _absence_, so a future author does not re-derive the
question.

The v2 trajectory assertion is purely additive and opt-in on every
runtime: `assert.sh` guards for an empty `EVAL_TRANSCRIPT` first, then
greps. On Antigravity the variable is simply never set, so trajectory
assertions no-op and artifact (v1) grading proceeds exactly as before —
nothing breaks; the feature is unavailable, not broken.

If a future `antigravity-cli` release adds a structured/stream output flag
that yields a locatable per-turn transcript, revisit this: at that point
mirror task 03's `EVAL_TRANSCRIPT` documentation into
`antigravity/.agents/workflows/evals.md` and delete this carve-out.

`antigravity/.agents/workflows/evals.md` carries a one-line pointer to
this file so the absence has a trace rather than being a silent skip.
