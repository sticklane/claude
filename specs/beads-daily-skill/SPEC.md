# /work — the skill that runs every session off the bd queue

Breakdown-ready: true
Rigor: prototype

Slug note: the directory keeps its original name (beads-daily-skill)
because task gates reference it; the skill itself is named `/work`.

## What it is, plainly

`/work` is one skill that answers the three questions every session
has: what should I do, how do I track what I am doing, and how do I
spread work across agents. Its answers: the bd queue, the bd queue,
and a native workflow the skill writes for you.

A session with it looks like this. You open a repo and say "what's
next." The skill runs `bd ready` and shows the unblocked tasks. You
pick one, or it takes the top one. It claims the issue in bd, does
the work, and closes the issue when done. If it finds new work along
the way, it files a bd issue linked to the task that surfaced it.
When it needs to understand unfamiliar code, it sends cheap scout
agents (Haiku tier, capped returns) rather than reading files into
the main context. If the work is genuinely parallel — review five
modules, fix twelve call sites — it writes a short native workflow
script, scouts on cheap models, judgment on the session model, runs
it, and files the surviving results as bd issues before they
evaporate. When you come back tomorrow and say "what's next," the
queue already knows where everything stands. There are no handoff
files.

Two mechanisms back it, so none of this depends on the model
remembering to cooperate:

- **The compliance Stop hook.** A session cannot end "done" while bd
  issues it claimed are still open. Forgetting the tracker becomes a
  refusal, not a quiet drift.
- **The pre-flight fan-out guard.** Before the skill runs a workflow
  it wrote, a small script estimates agent count times the measured
  per-agent floor; above a configured threshold it requires an
  explicit override.

The injection screen (screen-stub.sh) applies to any tracker-sourced
text the skill puts into a workflow prompt.

Code exploration note (maintainer direction, 2026-07-22): ctx is
deprioritized and is NOT part of this skill or the standard install.
The exploration default is cheap scout agents. ctx remains a
standalone product; integrating it is revisited when it earns its
place in this flow.

## Installation in other repos

Once per machine:

1. The plugin: `agentic@agentic-toolkit` (skills, agents, rules —
   including `/work`, `/onboard`, `/gate`, and the judgment skills).
2. `bd`, pinned 1.1.0 (`brew install beads`, per the recorded core
   task 02 decision).

Per repo, owned by an extended `/onboard` (this spec adds the bd
steps to the existing onboard flow):

1. `bd init`, curated: keep the AGENTS.md snippet it writes, gitignore
   `.beads/interactions.jsonl`, commit the `issues.jsonl` export.
2. `/gate` installs the Stop hook with the bd-compliance check
   included, plus format-on-edit if wanted.
3. Settings allowlist: `Bash(bd *)` — the grant class whose absence
   measurably killed tool adoption before.
4. Seed the queue: file the repo's first epics and issues from
   whatever plan exists, so `bd ready` has answers on day one.

Verification, per repo, before calling the install done: `bd ready`
returns; "what's next" triggers `/work`; the Stop hook blocks a
fixture claimed-open "done".

## CUJs — tested as part of the work, not assumed

Each journey is run live and recorded; the mechanical ones also get
eval scenarios. Live runs happen on TWO repos: this one and one real
consuming repo (e.g. ynab-mcp-server), because an install that only
works in its home repo is not an install.

- **CUJ-1 Fresh install.** Empty-queue repo → the per-repo steps →
  `bd ready` works and `/work` triggers on "what's next."
- **CUJ-2 Track and resume.** Start a task via `/work` (issue
  claimed); end the session with work unfinished — the hook allows
  exit only after the issue is closed, deferred with a note, or
  unclaimed; new session, "what's next" resumes from the queue with
  no re-explanation.
- **CUJ-3 Fan-out with scouts.** A genuinely parallel request → the
  skill writes a native workflow whose mechanical/scouting stages
  carry a cheap-tier `model:` option → results the run keeps are
  filed as bd issues before the session ends.
- **CUJ-4 Discovered work.** Mid-task, a worker surfaces a bug → it
  is filed as a bd issue with a discovered-from link to the task
  that surfaced it.
- **CUJ-5 Second repo.** Repeat CUJ-1 and CUJ-2 on the consuming
  repo, following only the written install steps — a test of the
  plan, not of the author.
- **CUJ-6 Portability read.** From a bare shell with no plugin, read
  the queue (`bd list --json` or the committed JSONL) and answer
  "what is in progress" — proving the data layer stands alone.

## Acceptance criteria

- [ ] the skill file exists as `/work` with trigger phrases covering
      "what's next", "work the queue", "track this", and fan-out
      asks; passes `bash evals/lint-ultra-gate.sh` if it mentions
      ultracode
- [ ] a fresh-session eval scenario (evals/, stub-CLI tier) shows the
      skill claiming before work, closing on done, and authoring a
      fan-out script whose mechanical stages carry a cheap-tier
      `model:` option
- [ ] a hook test: fixture session state with a claimed-open bd
      issue → the Stop hook blocks completion naming the issue;
      close it → the hook passes
- [ ] the pre-flight check, fed a fixture plan of 30 agents against a
      20-agent threshold, refuses without the override flag and
      passes with it
- [ ] `/onboard`'s flow includes the per-repo bd/gate/allowlist
      steps, and its doc names the once-per-machine prerequisites
- [ ] CUJ evidence: all six journeys run live, each with a short
      evidence note (commands, outputs, bd issue IDs) under this
      spec's `evidence/`; CUJ-1 and CUJ-2 on both repos, per CUJ-5
- [ ] AGENTS.md names `/work` as the attended daily default; the
      unattended queue mode is the same skill run headless

Next stage: none — implemented directly (2026-07-22, maintainer-
directed). Evidence under evidence/; the open remainder is CUJ-5's
consuming-repo run and CUJ-1's fresh-session trigger observation,
both marked MANUAL-PENDING in their evidence notes.
