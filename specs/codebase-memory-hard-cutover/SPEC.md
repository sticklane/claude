# Codebase-Memory hard cutover

Breakdown-ready: true

## Problem

The toolkit currently owns and routes code exploration through its Rust
`context-tree` implementation and `ctx` skill. The implementation duplicates a
broader upstream product, has low measured adoption, and makes this repository
responsible for parsers, indexing, reference resolution, MCP parity, durable
notes, and code-navigation policy.

The maintainer chose an immediate replacement with Codebase-Memory (CBM):
there is no compatibility window, notes companion, or retained ctx history.
The conversion must still leave installation deterministic, keep runtime
configuration under this toolkit's control, and prevent an upstream installer
from rewriting users' agent configuration.

## Solution

Make the headless `codebase-memory-mcp` v0.9.0 binary the toolkit's only
codebase index. Ship a checksum-pinned binary installer and bundled MCP
configuration, replace the canonical code-exploration skill and all live
routing with CBM's graph tools, migrate usage telemetry and audit language,
and delete `context-tree` plus ctx-only skills, tests, evals, docs, specs, and
cached repository state.

The toolkit owns only the release pin, installation, MCP declaration,
workflow doctrine, and validation. It does not run CBM's broad `install`,
`update`, or `uninstall` commands and does not install CBM-authored skills,
agents, or hooks.

## Requirements

### R1. Deterministic binary installation

Add a POSIX installer for the v0.9.0 headless release archives on macOS and
Linux, for both AMD64 and ARM64. The release version, asset names, and SHA-256
digests must be explicit, reviewable repository data.

The installer must:

- default to `~/.local/bin` while accepting an explicit destination;
- select the archive only from normalized `uname` OS/architecture values;
- download from the immutable v0.9.0 GitHub release URL;
- verify SHA-256 before extraction or replacement;
- install atomically and preserve an existing binary on any failure;
- support a network-free dry run that reports the selected version, asset,
  digest, and destination;
- never pipe a remote script to a shell; and
- never invoke CBM's client-configuring `install`, self-`update`, or broad
  `uninstall` commands.

Install a toolkit launcher named `agentic-codebase-memory-mcp` beside the
upstream binary. The launcher must fail closed unless `CBM_ALLOWED_ROOT` is
already set or the launch directory resolves to a Git root. It must export
that resolved absolute root and use the account-wide toolkit cache
`${XDG_CACHE_HOME:-$HOME/.cache}/agentic/codebase-memory` unless an explicit
`CBM_CACHE_DIR` is supplied. A single account-wide cache is intentional:
upstream requires concurrent CBM processes to share one canonical cache root,
while `CBM_ALLOWED_ROOT` remains session-specific. Uninstall/cleanup guidance
must name this cache path and must not delete it automatically.

The Windows runtime guide must use the same pinned release and checksum
principle. A new PowerShell installer is not required in this cutover.

### R2. Toolkit-owned MCP configuration

Add two schema-specific bundled MCP declarations:

- root `.mcp.json` uses Claude Code's documented wrapped `mcpServers` shape,
  defines the exact server key `codebase-memory-mcp`, launches
  `agentic-codebase-memory-mcp`, and passes
  `CBM_ALLOWED_ROOT=${CLAUDE_PROJECT_DIR}`;
- `.codex-plugin/plugin.json` uses Codex's documented inline `mcpServers`
  object, with a direct server map defining the same exact key and launcher.

Claude Code auto-discovers `.mcp.json` at the plugin root; its manifest needs
no invented field. Codex reads the explicit inline manifest object; this
avoids a filename collision because its companion `.mcp.json` accepts a
different wrapper than Claude Code's file. Antigravity documentation must give its native `/mcp` or
`mcp_config.json` registration because its validated plugin schema contains
only `$schema`, `name`, and `description` and has no bundled-MCP field.

The launcher derives Codex's active Git root from the MCP process working
directory and refuses to start outside a Git worktree unless
`CBM_ALLOWED_ROOT` is explicitly configured. Isolated packaging tests must
copy/install each plugin shape and assert the exact server command,
environment, and manifest path that the runtime will load.

The configuration must not enable the optional UI, commit
`.codebase-memory/graph.db.zst`, mutate global client files, or enable
automatic indexing for new repositories. The skill may explicitly call
`index_repository` for the active repository when no index exists.

### R3. Codebase-Memory exploration contract

Replace `.claude/skills/ctx/` with a canonical
`.claude/skills/codebase-memory/` skill and regenerate the regular-file
runtime entrypoints. The skill must use CBM's documented tool names and encode
progressive disclosure:

1. identify or index the active project;
2. use `get_architecture` for orientation;
3. use `get_graph_schema` before nontrivial graph queries;
4. use `search_graph` to resolve qualified symbols;
5. use `trace_path` and `detect_changes` for callers and impact;
6. use `get_code_snippet` only after locating a symbol; and
7. use `search_code` or bounded direct source search for content questions.

Negative and exhaustive claims must check project identity, current index
status, relevant pagination, and source coverage. A clean graph result is not
proof of textual absence; skipped, ignored, unparsed, and unindexed paths
require bounded direct source verification.

Remove the retired notes, zones, `ctx` command, `.context`, and exact-reference
contracts rather than presenting unsupported CBM equivalents.

### R4. Live workflow routing

Update all live rules, agents, skills, onboarding, runtime guides, and package
orientation so structural code questions route to Codebase-Memory before
whole-file reads when the MCP server is available. Scouts and critics must
receive the minimum read-only CBM tool surface their runtime supports and
must return distilled evidence rather than raw graph output.

Add `config/codebase-memory-routing-paths.txt` as the exact retained-surface
contract. It must enumerate the two code-discipline rules; scout and critic
agents; build, build-reference, breakdown, onboard, clone-audit, and work
skills; `AGENTS.md`, `CLAUDE.md`, and the repository README; the Claude Code,
Codex, and Antigravity install/runtime guides; `agentic audit`; `agentprof`;
and eval coverage. The integration test must check the required CBM-first,
bounded fallback, and parent-to-child evidence clauses in each applicable
surface. It must also assert that Antigravity's guide contains its native
`/mcp` or `mcp_config.json` registration and never substitutes another
runtime's command.

Where a runtime cannot grant an MCP server safely to a child agent, the
orchestrator must query CBM first and pass project identity, qualified
symbols, paths, index/coverage state, and graph evidence in the child prompt.
Do not invent an MCP tool grant in an agent frontmatter schema that does not
document one.

When CBM is unavailable, workflows must fall back to `rg` plus bounded file
reads without claiming index coverage. A missing optional backend must not
block unrelated pipeline work.

### R5. Telemetry and audit semantics

Replace ctx-specific `agentprof` usage parsing, exported schema fields, cost
summary labels, and tests with Codebase-Memory equivalents. Count the
canonical skill invocation and CBM MCP/CLI query tools without counting
generic variables named `ctx`.

Update `agentic audit` so its code-exploration check recognizes CBM use and
counts raw `Grep` or grep-led shell searches that occur before the first CBM
query in each transcript. This is deliberately an ordering/adoption signal:
it does not infer search boundedness or backend availability from transcript
text. Preserve the audit's read-only behavior.

### R6. Hard removal

Add `config/ctx-retirement-paths.txt`, with one exact repository-relative
tracked path or directory per line, as the deletion authority. It must
enumerate the implementation, tracked cache, canonical/generated skill,
evals, capability tests, old ctx research/guides, all twelve top-level ctx
spec families, and any individual ctx-only task/evidence files inside retained
spec families. The test must reject a retirement target that overlaps this
cutover spec, its evidence, generic context-budget fixtures, or non-ctx code.

Delete every path in that manifest from the working tree. “No retained
history” means those historical artifacts no longer exist in the current
tracked tree; rewriting Git object history is not part of this conversion.
The retirement manifest remains as the reviewable record of what was removed.

Remove or rewrite incoming references from retained docs, specs, inventories,
queue views, tests, and manifests. The absence test must use explicit product
tokens and an allowlist for this cutover spec, its evidence, the retirement
manifest, and current adoption research. It must not mass-rename ordinary
Go/Rust `context` variables, session-refresh context-budget fixtures, or prose
where “context” has its normal meaning.

Before editing or deleting, record the active-agent/worktree inventory and
the subset of retirement/live-routing paths already dirty. A dirty path
inside the retirement manifest is deleted only after its diff is read and one
of these ownership facts is recorded: it was produced by this cutover, the
current maintainer directive explicitly supersedes the ctx-only content and
no foreign live session owns it, or its owner confirms deletion. Stop on
another-session ownership or any unexplained diff. For every other dirty path,
read and merge its current diff before editing; stop rather than overwrite an
unexplained conflicting hunk. No bulk replacement from a clean checkout is
allowed.

### R7. Verification and packaging

Add deterministic tests that prove:

- all four supported platform tuples select the expected immutable asset and
  digest from fixture-driven `uname` results;
- dry run makes no network call, and an unsupported tuple fails before
  download;
- a mocked successful archive install replaces both binaries atomically,
  while a checksum mismatch or extraction failure leaves existing
  destinations byte-identical;
- the launcher resolves a temporary Git root, sets the exact allowed-root and
  toolkit-cache environment for a stub CBM process, and refuses a non-Git
  directory;
- isolated Claude and Codex plugin copies discover the exact
  `codebase-memory-mcp` server key, their schema-specific declarations, and
  launcher command; Antigravity's manifest remains schema-valid without an
  invented MCP field and its guide carries the native registration;
- every path in `config/codebase-memory-routing-paths.txt` carries its
  applicable CBM-first, bounded-fallback, or parent-handoff contract;
- the canonical and generated Codebase-Memory skills are current;
- the retirement manifest contains only reviewed paths, every listed path is
  absent, and no non-allowlisted tracked ctx product reference remains;
- agentprof and audit recognize Codebase-Memory; and
- the standard repository check and all plugin validators pass.

Tests must not download CBM or mutate real user configuration.

Add deterministic skill-contract fixtures for an ambiguous symbol, incomplete
coverage, a paginated result, a stale/uncommitted source edit, and a
graph-empty/text-present result. They must assert the documented query order
and bounded direct-source fallback. Replace the old ctx eval scenarios with
Codebase-Memory scenarios that exercise the same failure boundaries.

Run one live smoke test outside the network-free standard gate. On a supported
host, the test must download the repository-pinned v0.9.0 archive, verify the
archive digest itself against the selected platform pin before extraction,
and install only into a temporary directory. It must index a temporary fixture
repository and successfully execute
`get_architecture`, `get_graph_schema`, `search_graph`, and
`get_code_snippet`; all generated graph state stays under that temporary
directory. Unsupported hosts are manual-pending rather than a false pass. Save
the supported-host run and query observations in
`specs/codebase-memory-hard-cutover/evidence/live-smoke.md`.

## Out of scope

- Forking or modifying upstream Codebase-Memory.
- Bundling the graph UI.
- Committing or sharing generated CBM graph databases.
- Migrating `.context/notes`, zones, or ctx caches.
- Installing CBM's upstream skills, agents, instructions, or hooks.
- Automatic self-updates.
- A Windows PowerShell installer.

## Acceptance criteria

- `bash tests/test_codebase_memory_integration.sh` exits 0 and runs the
  enumerated installer, launcher, MCP packaging, and skill-contract fixtures
  for R1–R4 without network access or user-config writes. (L2)
- `bash tests/test_no_ctx_surface.sh` exits 0 after checking an explicit
  retirement manifest and bounded live-reference allowlist, while permitting
  generic programming uses of “context” and `ctx`. (L2)
- `bash tests/test_codebase_memory_live.sh` exits 0 when passed a
  supported host, verifies the downloaded archive against the repository pin,
  and performs the four real CBM user-flow queries in temporary fixture/cache
  roots without touching the checkout or user configuration. (L3)
- `rg -n -A8 '^## Antigravity registration$' antigravity/README.md |
  rg -q '/mcp|mcp_config\\.json'` exits 0.
  Depth ceiling: L1 is the deepest deterministic check for prose-only
  runtime instructions; the behavioral complement is the named verifier
  judgment that the command uses Antigravity's documented native surface.
- `bash agentprof/scripts/check.sh` exits 0 with Codebase-Memory usage and
  cost-summary tests green. (L3)
- `python3 -m pytest -q tests/test_agentic_audit.py
  tests/test_agentic_cli_retirement.py` exits 0. (L3)
- `bash tests/test_codex_skill_entrypoints.sh` exits 0 and reports generated
  entrypoints current. (L2)
- `python3 ~/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py
  .` exits 0. (L2)
- `claude plugin validate .` exits 0. (L2)
- `agy plugin validate .` exits 0. (L2)
- `bash scripts/check.sh` exits 0. (L3)

## Open questions

None.

## Parallelization

The conversion is deliberately one task. Distribution, routing, telemetry,
and deletion share one backend identity and one retirement boundary; splitting
them would create a staged cutover that the maintainer explicitly rejected.
Within the task, independent test fixtures may be prepared together, but one
worker owns all tracked edits and the final hard-removal sweep.
