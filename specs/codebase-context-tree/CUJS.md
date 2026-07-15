# Critical user journeys — codebase context tree

Status: CONFIRMED (two adversarial passes, 2026-07-15 — one attacking
journey selection, one walking each journey through SPEC.md; all findings
applied to this doc and to the spec in the same commit series)
Companion to SPEC.md. The primary user is a coding agent mid-task; the
human maintainer is the gating user for adoption (init, hooks, pruning).
The thesis every journey serves: always-up-to-date codebase context,
minimal tokens.

The adversarial pass inverted the draft's emphasis, and the tiering below
records that correction: ranked maps and symbol lookup are table stakes —
Aider auto-injects a repo map and Serena serves LSP symbol queries today —
so this tool must merely MATCH them there. What no shipping tool does is
tier 1: zero-token freshness and a closed knowledge loop.

## Tier 1 — Differentiators (the thesis carriers)

### CUJ6 — Trust the answer after the repo changed

Trigger, in frequency order: the agent's OWN edits mid-task; a `git
pull`/merge; a parallel agent; a human editing in an IDE alongside.
Journey: nothing — the next query's staleness sweep reparses exactly the
changed files and answers from current state. This includes the write-path
self-check: after adding a function, `ctx sig` confirms it parsed and
landed in the tree. No re-index command, no token spent re-orienting.
Honest guarantee: results are current "as of the last completed sync" —
a query racing an in-flight sync reads the pre-completion snapshot (C6),
and the no-VCS baseline's mtime+size scan carries a racy-edit guard (R2)
rather than a proof. Single-editor sessions see exact freshness.
Design mapping: R2, R3, C5, C6, R16.

### CUJ4 — Leave knowledge where the next agent will find it

Trigger: agent learns something non-obvious the hard way (an invariant, a
gotcha, why a workaround exists).
Journey: `ctx notes add <symbol> "..." --kind gotcha` → knowledge anchors
to the symbol it's about, versioned with the repo, reviewable in the PR
diff. C3 rejects ambiguous anchors with a candidate list (exit 3), so the
write lands on the right symbol or fails loudly — the draft's happy-path
framing hid that rejection loop.
Token economics: ~50 tokens once; the alternative — a CLAUDE.md bullet —
is re-sent in EVERY future session whether relevant or not, and
directory-scoped memory can't target a function.
Design mapping: R12, R14, C9, C3.

### CUJ5 — Encounter that knowledge at the right moment

Trigger: a later agent is about to touch a symbol carrying a note it
doesn't know exists.
Journey: every structure query the agent already runs (`ctx tree`, `ctx
sig`, `ctx map`, `ctx at`) marks note-carrying symbols with
`[notes:<count>]`, `!`-flagged when stale (C10) — so note existence
reaches the agent BEFORE the edit, unprompted, for ~5 tokens; one
`ctx notes <symbol>` pull retrieves the content.
This was the draft's biggest gap: pull-only notes made CUJ4 write-only
and the whole knowledge loop dead on arrival. Both adversarial passes
independently ranked it the linchpin; C10 is now spec, not a hope.
Design mapping: C10 in R6/R7/R8/R19, R12.

### CUJ7 — Keep notes honest through refactoring

Trigger: a refactor renames/moves/edits a symbol that carries notes.
Journey: sync re-anchors deterministically (rename via body hash; move+
rename+edit via tree-diff) — queries see it immediately via the index —
and the new anchor path is written into the note file at a persistence
point: the pre-commit hook stages it into the same commit as the refactor
that caused it (or `ctx sync --write-anchors` for hook-less setups), so
committed re-anchors survive clones and index rebuilds while read-only
queries never mutate tracked files.
A body change flips derived freshness to stale with a diff pointer; the
NEXT agent that reads the note revalidates it as part of work it was
already doing. Freshness derives from note file + working tree alone
(R12), so no cache loss can fake freshness.
Token economics: maintenance is zero-token; revalidation judgment is
spent only at read time, attached to a session already paying for that
context.
Design mapping: R13 (durable anchor-path persistence — added after the
coverage pass showed tree-diff re-anchors died on every fresh clone),
R12, `ctx notes list --stale`.

### CUJ9 — From a stack trace to the code that owns it

Trigger: a test failure or stack trace names `file.py:217`; the agent
needs the owning symbol, its signature, and any warnings before touching
it.
Journey: `ctx at file.py:217` → containment chain (module → class →
innermost function) with kinds, signatures, and note markers — the
symbol-world entry point for position-world evidence, and the feeder for
CUJ2/CUJ3/CUJ5. Positions in files the index skips (ignored, generated,
unsupported extension) fail fast with a one-line reason and exit 4 rather
than guessing — stack traces routinely point at such files.
This journey was missing from the draft entirely; the selection pass
ranked debugging navigation above blast-radius in real frequency, and no
existing verb accepted file:line. R19 was added to the spec for it.
Token economics: ~100 tokens vs reading the file around the line (~2-4k).
Design mapping: R19 (new), C10.

## Tier 2 — Table stakes (match Aider/Serena, don't lose)

### CUJ1 — Orient in an unfamiliar repo

Journey: `ctx map --tokens 1000` → ranked overview; drill down with
`ctx tree <path> --depth 2 --limit N` (result-capped with a truncation
count — depth alone left output unbounded, breaking every token claim on
big subtrees).
Token economics: ≤1.5k tokens vs 10-50k of orientation reads or 2-4 scout
dispatches. On a repo with a good AGENTS.md map, `ctx map`'s edge is
currency (never stale) and rank (reference-weighted), not raw size.
Design mapping: R8 (C7 budget), R6 (depth + result caps).

### CUJ2 — Inspect a symbol before using or changing it

Precondition (named honestly): the agent has a name or position — from
CUJ1 browsing, CUJ9's `ctx at`, or C3 suffix matching. This is the most
FREQUENT query verb, not the thesis carrier the draft crowned it.
Journey: `ctx sig auth.login.authenticate --doc` (~100 tokens) →
signature + docstring + note marker; Read the file slice at the returned
position only if the body is actually needed.
Design mapping: R7, R1 (positions), C3, C10.

### CUJ3 — Assess blast radius before a change

Journey: `ctx refs <symbol> --limit N` (callers, labeled
heuristic/precise, capped with truncation count) + `ctx deps <path>
--reverse` → affected sites enumerated before editing; labels tell the
agent when the list is trustworthy vs indicative (R11 upgrades to
precise under LSP).
Design mapping: R9, R10 (caps added post-pass), R11.

### CUJ8 — Brief a subagent compactly

Journey: orchestrator embeds `ctx tree services/foo --depth 2` + `ctx
sig` lines (~300 tokens, caps make the bound real) in the dispatch prompt
instead of file dumps or "go explore".
Honest cost note: MCP registration loads ~8 tool schemas (~1-2k tokens)
into every session whether used or not — the CLI path through Bash is the
cheaper door for token-sensitive harnesses, and the README's integration
snippet (R17) says so.
Design mapping: R6-R8, `--json`, R15/R17.

## Tier 3 — Enabling journeys (adoption and upkeep)

### CUJ0 — The tool is in the agent's hands at all

The whole thesis rides on this: a tool the agent doesn't reach for saves
nothing. v1 ships the minimal routing story — R17's README carries a
copy-paste CLAUDE.md/AGENTS.md snippet for consuming repos ("structure
questions → ctx before file reads or scout dispatch") plus MCP
registration instructions — so adoption is a paste, not a doctrine
project. Changing THIS toolkit's own token-discipline routing stays
post-v1 (Out of scope), but nothing blocks a consuming repo from wiring
it on day one.
Design mapping: R17 (extended post-pass), R15.

### CUJ10 — Maintainer audits and prunes the note store

Trigger: notes accumulate; some go stale and stay stale (the system
never deletes — R13), and unpruned graveyards erode CUJ5's trust.
Journey: `ctx notes list --stale` → human (or an agent instructed by
one) reviews, rewrites, or deletes note FILES like any other tracked
file, in a normal PR the team reviews. No new machinery: plain file ops

- VCS.
  Design mapping: R12 (list/filter), R14 (plain-VCS semantics), C9
  (provenance says who wrote what when).

### CUJ11 — Recover from a broken index

Trigger: index corruption, schema migration, or plain doubt.
Journey: delete `.context/cache/` and run any query — the index is
derived state, rebuilt deterministically from source + notes; committed
re-anchors survive because anchor paths live in note frontmatter once
persisted (R13 phase 2), and freshness re-derives from file + tree (R12).
The only loss window is a re-anchor computed but not yet written at a
persistence point.
Design mapping: C4 (cache/ is derived), R12/R13 durability, rebuild leg
of the R13 acceptance criterion.

## Cross-cutting invariant — scale

Formerly a journey; the selection pass correctly demoted it: same
actions, bigger repo. The invariant: TOKEN cost of every journey is
identical at 1k and 100k files (caps and subtree scoping see to it).
LATENCY is bounded by changed files once synced; the per-query staleness
scan is O(tree) stats in the baseline — honest number: seconds, not
milliseconds, at 100k files without acceleration — which is why
`ctx hooks install` enables git's fsmonitor (R16, staffed post-pass) and
why 100M-file ecosystems arrive via VCS-adapter change feeds, not the
baseline scan.

## Non-journeys (explicitly not served, by design)

- "Find code about X" semantic/fuzzy search → claude-context / grep
  (Out of scope; docs/guides/large-codebase-context.md routes it).
- Deep-reading a function body — ctx locates and describes; Read owns
  content.
- Reviewer-orients-on-a-diff: composable from `ctx at` + `ctx refs` +
  notes today; a dedicated diff view is post-v1 if demand shows up.
- Cross-repo context, editing/refactoring execution, CI integration.

## Coverage verdict (post-fix)

| CUJ                      | Status after spec amendments                                        |
| ------------------------ | ------------------------------------------------------------------- |
| 0 adoption               | delivered via R17 snippet + R15 (was: acknowledged gap)             |
| 1 orient                 | delivered (R6 result cap added)                                     |
| 2 inspect                | delivered (precondition named)                                      |
| 3 blast radius           | delivered (R10 cap added)                                           |
| 4 leave note             | delivered                                                           |
| 5 encounter note         | delivered via C10 markers (was: broken, pull-only)                  |
| 6 trust freshness        | delivered with honest "last completed sync" bound                   |
| 7 notes through refactor | delivered via durable anchor persistence (was: died on fresh clone) |
| 8 brief subagent         | delivered (caps make the bound real; MCP cost named)                |
| 9 stack trace → symbol   | delivered via R19 (was: missing entirely)                           |
| 10 maintainer prune      | delivered (no new machinery needed)                                 |
| 11 recovery              | delivered (derived-state property)                                  |
