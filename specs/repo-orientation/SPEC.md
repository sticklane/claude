# Repo orientation for agents: map, state, and interop

## Problem

A fresh agent landing in this repo has no single entry point that says
what the repo is, where things live, and what work is open. Orientation
is scattered: CLAUDE.md (43 lines) carries conventions but no structure
map; README.md (185 lines) explains the pipeline for humans; live work
state exists only as `Status:` headers across 30 task files (QUEUE.md is
the plan view, deliberately not live state); handoff files have a
defined format but nothing indexes where they land. And the toolkit's
own skills teach only part of what the four vendors now converge on:
/onboard writes a verified, ≤200-line CLAUDE.md with a pruning test —
but says nothing about a structure map, per-directory context files for
large repos, cross-tool AGENTS.md interop, or where open work lives.
The maintainer wants both fixed: this repo follows the best practices,
and the skills encode them for every repo the toolkit touches.

## Solution

Research recorded by this spec in docs/external-playbooks.md (R5 carries
the content and sources). The four vendors converge on: a small
always-on root context file (Anthropic: target <200 lines; OpenAI
Codex: 32 KiB hard cap); pointers and just-in-time retrieval instead of
content dumps (Anthropic: exclude "file-by-file descriptions", keep
"lightweight identifiers"); hierarchy with nearest-file-wins for depth
(Codex nested AGENTS.md, gemini-cli GEMINI.md hierarchy, Claude Code
on-demand subdirectory CLAUDE.md); structured work-state files (Kiro's
requirements/design/tasks with checkbox state — validating this repo's
specs/ + Status headers); and AGENTS.md as the cross-tool interop
standard (Linux Foundation stewarded; read natively by Codex, Jules,
Kiro CLI, Android Studio; gemini-cli via `context.fileName`; Claude
Code via `@AGENTS.md` import).

Four decisions, recommended options adopted (non-interactive fallback,
each reversible before implementation): (1) orientation lives in a NEW
root `AGENTS.md` (≤60 lines: repo map, state pointers, verified
commands) and CLAUDE.md gains one `@AGENTS.md` import line — Claude
sessions load it via the documented import mechanism, other tools read
it natively, nothing is duplicated; (2) the live work-state view is a
deterministic script, `specs/status.sh`, deriving the dashboard from
task `Status:` headers on demand — state keeps its single source (the
headers), so nothing drifts, and rendering is code, not model calls;
(3) /onboard gains the four missing practices (structure-map bullet,
per-directory CLAUDE.md guidance for monorepos, an AGENTS.md interop
offer, a work-state pointer); (4) /handoff's artifact location gets
indexed in AGENTS.md's State section rather than a new discovery
mechanism. Marker phrases ("Repo map", "status.sh", "per-directory
CLAUDE.md", "@AGENTS.md", and AGENTS.md anywhere in CLAUDE.md or the
onboard skill) do not exist in the implementation targets today, so the
acceptance greps below cannot pass vacuously.

## Requirements

- R1 (root AGENTS.md): `AGENTS.md` exists at the repo root, ≤60 lines,
  opening with 2–3 sentences naming the repo's purpose and that
  authoring conventions and always-on rules live in CLAUDE.md and
  `.claude/rules/`, then exactly three sections:
  - `## Repo map` — one pointer line per top-level area (`.claude/`
    skills/agents/rules, `.claude-plugin/`, `antigravity/`, `specs/`
    with QUEUE.md called out, `docs/`, `evals/`, and any other
    top-level directory existing at implementation time, e.g.
    `runtimes/` if the model-agnostic spec has landed). Pointers, not
    descriptions — path plus one clause on what lives there; never
    file-by-file content.
  - `## State` — where live state lives: task-file `Status:` headers
    are canonical; `specs/QUEUE.md` is the wave plan (not live state);
    `specs/status.sh` renders the dashboard on demand; in-flight
    session handoffs land as `HANDOFF.md` next to the active task/spec
    file (or `.claude/HANDOFF.md`).
  - `## Commands` — the repo's verified commands only, each with a
    half-line on what it proves, and every listed command RE-RUN at
    implementation time (a context file that lies is worse than none —
    the onboard doctrine applies to us too). Candidates:
    `./evals/run.sh <skill>`, `./specs/status.sh`, and
    `claude plugin validate .` — the last one currently exits non-zero
    (review-fixes task 01 owns the fix), so it is listed only if that
    task has landed; the decomposition carries the `Depends on:` line.
- R2 (CLAUDE.md interop): CLAUDE.md's first 10 lines gain one line
  containing `@AGENTS.md` — the Anthropic-documented import so Claude
  sessions load the orientation file at launch. If the implementing
  session verifies the import does not resolve in a target harness,
  the same line stays as a plain pointer sentence (the grep is
  identical either way). No orientation content is duplicated into
  CLAUDE.md; CLAUDE.md stays ≤200 lines (budget shared with the
  context-management spec's R1).
- R3 (state dashboard): `specs/status.sh` exists, is executable, and:
  - takes no arguments; scans `specs/*/tasks/*.md`, reading each
    file's status as the FIRST line matching `^Status:` anywhere in
    the file (not just a top header block — one current file,
    `specs/skill-evals/tasks/01-evals-harness.md`, carries its Status
    line below a comment block); a file with no `Status:` line prints
    status `none`;
  - prints one row per task file containing the status value and the
    file path, then a `TOTAL` summary section with one `<status>: <n>`
    line per distinct status found;
  - derives everything from the headers, writes nothing, needs only
    POSIX shell + grep/sed/sort (no jq, no network);
  - exits 0 when specs/ contains no task files (prints an empty-queue
    notice), and exits 0 on a normal run;
  - stays ≤40 lines so it is reviewable at a glance.
  Ready-to-dispatch computation (Depends-on resolution) is explicitly
  NOT this script's job — that logic stays in /drain (Out of scope).
- R4 (onboard encodes the practices): `.claude/skills/onboard/SKILL.md`
  gains, in its existing structure (the Include list, and step 5's
  offers):
  - an Include bullet containing "repo map": a short repo map — one
    pointer line per top-level area — never file-by-file descriptions
    (extends the existing exclusion, does not restate it);
  - a monorepo/large-repo note containing "per-directory CLAUDE.md":
    subsystem detail belongs in per-directory CLAUDE.md files, which
    load on demand when files there are read; the root map stays
    small;
  - a step-5 offer containing "AGENTS.md": offer a root AGENTS.md
    interop file (pointer-only, mirroring nothing that would drift)
    for cross-tool compatibility — Codex, Jules, and Kiro read it
    natively, gemini-cli via `context.fileName`, Claude Code via
    `@AGENTS.md` import;
  - an Include bullet for work state: if the repo uses the spec
    pipeline, name where open work lives (specs/, task `Status:`
    headers, and the status script if present).
- R5 (research record): `docs/external-playbooks.md` gains a `## Repo
  orientation for agents` section recording, with source links: the
  four-vendor convergence — small always-on root file (Anthropic
  memory docs: target under 200 lines, code.claude.com/docs/en/memory;
  Codex: 32 KiB `project_doc_max_bytes` cap,
  developers.openai.com/codex/guides/agents-md), pointers/JIT over
  content (Anthropic best-practices: exclude file-by-file
  descriptions; context-engineering post: "lightweight identifiers"),
  nearest-file-wins hierarchy for depth (nested AGENTS.md at
  agents.md; gemini-cli GEMINI.md hierarchy; Claude Code on-demand
  subdirectory CLAUDE.md, code.claude.com/docs/en/large-codebases),
  structured work-state files (Kiro specs: requirements/design/tasks,
  kiro.dev/docs/specs; steering files product/tech/structure,
  kiro.dev/docs/steering), and AGENTS.md as the interop standard
  (Linux Foundation; native in Codex/Jules/Kiro/Android Studio;
  gemini-cli only via `context.fileName`; Claude Code via import or
  symlink). Divergences recorded: inclusion modes (Kiro
  always/fileMatch/manual vs Claude Code `paths:` rules) and
  AGENTS.md-by-default (not honored by gemini-cli). One line on
  llms.txt: published by vendors for their own doc sites; no coding
  tool consumes a repo's llms.txt — skipped here.
- R6 (mirrors): `antigravity/.agents/skills/onboard/SKILL.md` mirrors
  R4's repo-map, per-directory, and work-state bullets (AGENTS.md is
  already Antigravity's native context file, so the interop offer is
  replaced by one sentence saying exactly that). The root `AGENTS.md`
  from R1 is a toolkit-repo artifact, not part of the antigravity
  port — no mirror.
- R7 (versioning): the implementing change bumps `plugin.json`'s minor
  version by one from the value it finds, unless landing in a
  commit-set whose other specs already carry a single combined bump.

## Out of scope

- Per-directory CLAUDE.md files in THIS repo — at 43 root lines and a
  shallow tree, the root map suffices; the practice ships as /onboard
  guidance for repos that need it.
- llms.txt — no coding tool consumes a repo's llms.txt today; recorded
  in R5 and skipped.
- LSP/code-intelligence plugins, auto-memory (MEMORY.md), compaction
  steering — harness features; compaction steering is owned by the
  context-management spec.
- /drain consuming `specs/status.sh` — drain keeps its own header
  parsing (its inventory contract is under the review-fix wave);
  the script serves humans and fresh sessions, not the orchestrator.
- Restructuring CLAUDE.md's content into AGENTS.md — conventions stay
  in CLAUDE.md (authoritative for Claude sessions and edited by
  several queued tasks); AGENTS.md is orientation and interop only.
- Kiro steering-file or GEMINI.md ports — the porting guide
  (model-agnostic spec) owns runtime mapping; AGENTS.md covers interop
  here.

## Acceptance criteria

- [ ] `test -f AGENTS.md && grep -q "^## Repo map" AGENTS.md && grep -q "^## State" AGENTS.md && grep -q "^## Commands" AGENTS.md && [ "$(wc -l < AGENTS.md)" -le 60 ]` (R1)
- [ ] `grep -q "specs/QUEUE.md" AGENTS.md && grep -q "status.sh" AGENTS.md && grep -q "HANDOFF.md" AGENTS.md && grep -q "Status:" AGENTS.md` (R1 State section content)
- [ ] `head -10 CLAUDE.md | grep -q "AGENTS.md" && [ "$(wc -l < CLAUDE.md)" -le 200 ]` (R2)
- [ ] `test -x specs/status.sh && bash -n specs/status.sh && [ "$(wc -l < specs/status.sh)" -le 40 ]` (R3)
- [ ] `out=$(mktemp) && ./specs/status.sh > "$out" && grep -q "TOTAL" "$out" && for f in specs/*/tasks/*.md; do grep -q "$f" "$out" || exit 1; done` — every task file appears, totals rendered (R3)
- [ ] `d=$(mktemp -d) && mkdir -p "$d/specs" && (cd "$d" && bash "$OLDPWD/specs/status.sh")` → exits 0 (R3 empty-queue path; run from the repo root so `$OLDPWD` resolves; the subshell's exit status is the line's status)
- [ ] `grep -qi "repo map" .claude/skills/onboard/SKILL.md && grep -q "per-directory CLAUDE.md" .claude/skills/onboard/SKILL.md && grep -q "AGENTS.md" .claude/skills/onboard/SKILL.md && grep -qi "open work" .claude/skills/onboard/SKILL.md` (R4)
- [ ] `sed -n '/[Rr]epo orientation for agents/,/^## /p' docs/external-playbooks.md | grep -qi "agents.md" && sed -n '/[Rr]epo orientation for agents/,/^## /p' docs/external-playbooks.md | grep -qi "kiro" && sed -n '/[Rr]epo orientation for agents/,/^## /p' docs/external-playbooks.md | grep -qi "llms.txt"` (R5, scoped to this spec's section)
- [ ] `grep -qi "repo map" antigravity/.agents/skills/onboard/SKILL.md && grep -q "per-directory" antigravity/.agents/skills/onboard/SKILL.md` (R6)
- [ ] plugin.json minor version strictly greater than the pre-implementation value, verified in the implementing task's evidence (R7)
- [ ] End to end: a fresh session (or a dry-read) that opens ONLY `AGENTS.md` and runs `./specs/status.sh` can answer: what this repo is, where skills/agents/rules/specs/docs live, which commands are verified, how many tasks are open and in what statuses, and where a handoff would be — without reading any other file.

## Open questions

(none — the four decisions are recorded in Solution; recommended
options adopted per the non-interactive fallback, reversible before
implementation.)

## Parallelization

Not yet decomposed — when /breakdown runs, its tasks join the combined
queue in [specs/QUEUE.md](../QUEUE.md) (single wave-plan copy there;
update its task count and wave table as part of decomposition). Three
of this spec's targets sit on QUEUE.md's declared serial chains, so
the decomposition must carry cross-spec `Depends on:` lines:
- `CLAUDE.md` (R2) — shares the ≤200-line budget and file with
  context-management 01 and chaining-antipatterns 02/03.
- `.claude/skills/onboard/SKILL.md` (R4) — also edited by
  chaining-antipatterns 02.
- `docs/external-playbooks.md` (R5) — the appenders serialize
  (QUEUE.md); R5 is a sixth append.
R1/R3 (new files) have no collisions and can dispatch in any wave.
