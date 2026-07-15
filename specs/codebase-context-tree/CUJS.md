# Critical user journeys — codebase context tree

Status: DRAFT pending adversarial confirmation
Companion to SPEC.md. The primary user is a coding agent mid-task; the
secondary user is the human maintainer supervising agents. The thesis
every journey serves: always-up-to-date codebase context, minimal tokens.
Each journey states the trigger, the path through the tool, the token
economics against today's status quo (Claude Code defaults: file reads,
grep, scout dispatches, CLAUDE.md), and the spec requirements that carry
it.

## CUJ0 — The tool is in the agent's hands at all

Trigger: any session in a ctx-enabled repo starts.
Journey: the harness exposes ctx (MCP tools registered, or CLI on PATH
with one CLAUDE.md line saying when to reach for it); the agent knows
structure questions go to ctx before file reads or scout dispatch.
Token economics: the whole thesis rides on this journey — a tool the
agent doesn't reach for saves nothing.
Design mapping: R15 (MCP), R17 (README); integration doctrine is
explicitly out of scope until post-v1 (Out of scope: token-discipline
routing). GAP CANDIDATE: nothing in v1 makes an agent discover or prefer
ctx.

## CUJ1 — Orient in an unfamiliar repo

Trigger: fresh session, unfamiliar or half-remembered codebase.
Journey: `ctx map --tokens 1000` → ranked overview of the most-referenced
symbols per component; agent picks the two subtrees that matter and goes
deeper with `ctx tree <path> --depth 2`.
Token economics: ≤1.5k tokens total. Status quo: reading README + AGENTS
map + opening 3–10 files (10–50k tokens) or 2–4 scout dispatches (~25k
subagent tokens each, minutes of latency).
Design mapping: R8 (ranked map, C7 budget), R6 (subtree outline).

## CUJ2 — Inspect a symbol before using or changing it

Trigger: agent is about to call, modify, or test a specific function.
Journey: `ctx sig auth.login.authenticate --doc` → signature + docstring
(~50–200 tokens); only if the body is actually needed does the agent Read
the file slice at the returned line.
Token economics: ~100 tokens vs reading a 400-line file (~4k tokens) to
see one signature. This is the highest-frequency journey.
Design mapping: R7 (sig/doc), R1 (positions for the follow-up slice
read), C3 (suffix lookup without knowing the full path).

## CUJ3 — Assess blast radius before a change

Trigger: agent plans a signature change, rename, or module move.
Journey: `ctx refs <symbol>` (callers, labeled heuristic/precise) +
`ctx deps <path> --reverse` (who imports this module) → agent enumerates
affected sites before editing.
Token economics: two queries, ~200–500 tokens, vs project-wide grep whose
raw output the agent must read and filter (1–10k tokens, false positives
included).
Design mapping: R9, R10, R11 (precision labeling so the agent knows when
the list is trustworthy vs indicative).

## CUJ4 — Leave knowledge where the next agent will find it

Trigger: agent learns something non-obvious the hard way (an invariant, a
gotcha, why a workaround exists).
Journey: `ctx notes add <symbol> "..." --kind gotcha` → knowledge is
anchored to the symbol it's about, versioned with the repo, visible in
the PR diff for human review.
Token economics: writing costs ~50 tokens once; the alternative — a
CLAUDE.md bullet — is re-sent in EVERY future session's context whether
relevant or not, and directory-scoped memory can't target a function.
Design mapping: R12, R14 (merge story), C9 (provenance).

## CUJ5 — Encounter that knowledge at the right moment

Trigger: a later agent is about to touch a symbol that carries a note it
doesn't know exists.
Journey: structure queries the agent already runs surface note presence —
the note reaches the agent BEFORE the edit, without the agent asking
"are there notes?".
Token economics: a one-line indicator (~5 tokens) piggybacking on queries
already made; the failure mode it prevents (re-learning the gotcha) costs
thousands.
Design mapping: R12 (`ctx notes <symbol>`) is pull-only. GAP CANDIDATE:
nothing in the spec pushes note existence into `ctx sig`/`ctx tree`/
`ctx map` output, so the journey only completes if the agent already
suspects a note exists.

## CUJ6 — Trust the answer after the repo changed

Trigger: mid-session `git pull`, a parallel agent's edits, or a human
editing in an IDE alongside; the agent queries afterward.
Journey: nothing — the next query's staleness sweep reparses exactly the
changed files and answers from current state. No re-index command, no
stale answer, no token spent re-orienting.
Token economics: zero tokens (CPU-side sweep); the status quo failure is
answering from a stale mental model and editing against code that moved.
Design mapping: R2, R3 (sweep on every query), C5 (journal), C6
(concurrent-sync safety), R16 (hooks pre-warm the burst).

## CUJ7 — Keep notes honest through refactoring

Trigger: a refactor renames/moves/edits a symbol that carries notes.
Journey: sync re-anchors deterministically (rename/move) or flags the
note stale with a pointer to what changed (body edit); the NEXT agent
that reads the note sees the stale flag plus diff pointer, revalidates or
rewrites it as part of work it was already doing.
Token economics: maintenance itself is zero-token; revalidation judgment
is spent only at read time, attached to a session already paying for that
context.
Design mapping: R13 (three-layer re-anchor, C2 hash), R12 (derived
freshness), `ctx notes list --stale` (the audit view).

## CUJ8 — Brief a subagent compactly

Trigger: an orchestrator dispatches a worker/scout into a subsystem.
Journey: orchestrator embeds `ctx tree services/foo --depth 2` + relevant
`ctx sig` lines (~300 tokens) in the dispatch prompt instead of file
dumps or "go explore" (which costs the child its own discovery pass).
Token economics: ~300 tokens per dispatch vs each child re-deriving
structure (~5–25k tokens per child, multiplied across a fleet).
Design mapping: R6–R8; `--json` for orchestrators that assemble prompts
programmatically.

## CUJ9 — Work a subtree of a huge repo

Trigger: agent's task lives in one service of a 100k-file monorepo.
Journey: all queries subtree-scoped; sync work bounded by changed files,
not repo size; the agent never pays for the 99k files it isn't touching.
Token economics: identical query costs at 1k and 100k files; the status
quo (grep/glob over the tree, orientation reads) degrades linearly with
repo size.
Design mapping: architecture rules (no whole-tree work), R2 (O(changed)
sync), R6 (subtree scoping), scale posture (100M headroom via adapters).

## Non-journeys (explicitly not served, by design)

- "Find code about X" semantic/fuzzy search → claude-context / grep
  (Out of scope; docs/guides/large-codebase-context.md routes it).
- Deep-reading a function body — ctx locates and describes; Read still
  owns content.
- Cross-repo context, editing/refactoring execution, CI integration.
