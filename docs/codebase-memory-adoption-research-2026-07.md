# Codebase-Memory adoption research

Verified: 2026-07-26

Research record for the toolkit's hard cutover to Codebase-Memory (CBM). This
document records current upstream facts, the adopted ownership boundary, and
the capability decisions behind the implementation spec.

## Recommendation

Use CBM as the sole code-navigation and analysis backend, integrated
it as a toolkit-owned, project-scoped MCP dependency. Do not run CBM's general
`install` workflow from this toolkit: that workflow is intentionally an
installer for many coding clients and writes MCP configuration, skills,
instructions, agents, and hooks outside this repository.

The safe distribution boundary is:

1. pin an upstream release and platform archive checksums;
2. install only the headless binary, without CBM's client configuration;
3. configure the MCP entry through this toolkit's runtime-specific package
   shape (Claude Code's root file and Codex's inline manifest object);
4. set `CBM_ALLOWED_ROOT` and an explicit toolkit-owned `CBM_CACHE_DIR`;
5. keep auto-indexing off until the user or a project-scoped setup command
   enables it; and
6. make upgrades reviewed version/checksum changes rather than invoking CBM's
   self-update command.

CBM supplies structural navigation, architecture, callers, impact analysis,
semantic and literal search, clone/dead-code discovery, and working-tree
change analysis. Unsupported symbol-note, named-zone, and direct
file-position contracts were deliberately dropped; the toolkit does not keep
a companion backend or present invented equivalents.

## Verified upstream facts

The first-party project is
[DeusData/codebase-memory-mcp](https://github.com/DeusData/codebase-memory-mcp)
and is [MIT licensed](https://github.com/DeusData/codebase-memory-mcp/blob/v0.9.0/LICENSE).
The executable and MCP command are both `codebase-memory-mcp`.

The current release is
[v0.9.0](https://github.com/DeusData/codebase-memory-mcp/releases/tag/v0.9.0),
published 2026-07-08. It provides immutable platform archives, a checksum
file, and release-asset digests. For example, the v0.9.0 headless macOS ARM64
archive has SHA-256
`faa02f0404230c451a9812230394481948f80183801fa5bf67044b41c2f25ed4`
in the release's
[checksums.txt](https://github.com/DeusData/codebase-memory-mcp/releases/download/v0.9.0/checksums.txt).
The release also publishes an SBOM. These are useful supply-chain inputs; an
installer still needs to fail closed when a downloaded archive does not match
the toolkit-pinned digest.

Upstream documents a single local binary, SQLite-backed persistent graphs,
15 MCP tools, 158 vendored tree-sitter grammars, graph/LSP-assisted call
resolution, BM25 and bundled local semantic search, architecture and impact
queries, code snippets, index-coverage checks, dead-code and near-clone
analysis, ADR management, and a one-shot CLI mode. The current feature and
operation claims are in the
[v0.9.0 README](https://github.com/DeusData/codebase-memory-mcp/blob/v0.9.0/README.md).
The claim that processing is local and telemetry-free is an upstream product
claim, not an independent audit performed for this repository.

The manual MCP shape is a stdio server with an absolute binary path and no
arguments. Upstream documents `CBM_ALLOWED_ROOT` as a resolved-path boundary
for indexing and `CBM_CACHE_DIR` as the home of indexes and runtime settings.
Its default cache is `~/.cache/codebase-memory-mcp`; runtime settings live in
`_config.db`. `auto_index` defaults to `false`, while the server's watcher can
keep an already-indexed active project current. See
[CONFIGURATION.md](https://github.com/DeusData/codebase-memory-mcp/blob/v0.9.0/docs/CONFIGURATION.md).

CBM can also write `.codebase-memory/graph.db.zst` and a `.gitattributes`
entry when the team-shared graph artifact is used. That artifact should be
off by default here: adding a generated binary graph to a user's repository
is a separate, explicit opt-in.

## Why the general installer is the wrong integration boundary

The release `install.sh` defaults to `~/.local/bin`, supports
`--skip-config`, and otherwise runs `codebase-memory-mcp install -y`.
The native install command detects clients and writes their MCP entries plus
durable augmentation. Upstream currently lists 43 client surfaces. Among
them, Claude Code receives user MCP configuration, skills, agents, and
hooks; Codex receives global configuration, instructions, agents, and
session hooks. The installer provides `install --dry-run`, but a dry run does
not make those writes part of this plugin's ownership model.

Letting both installers own the same runtime files would create three
problems:

- configuration precedence and removal would be ambiguous;
- CBM updates could change the toolkit's behavior without a toolkit release;
  and
- CBM's broad client detection would mutate runtimes the user did not ask
  this plugin to manage.

The toolkit should therefore use the binary-only path and own the small MCP
configuration it needs. It should neither pipe a mutable `main` branch script
to a shell nor invoke `install -y`, `update`, or broad `uninstall` as part of
normal setup.

Registry and package-manager installation is also a poor pinning mechanism
for the first integration. In the v0.9.0 source tag, the
[Homebrew formula](https://github.com/DeusData/codebase-memory-mcp/blob/v0.9.0/pkg/homebrew/Formula/codebase-memory-mcp.rb),
[PyPI metadata](https://github.com/DeusData/codebase-memory-mcp/blob/v0.9.0/pkg/pypi/pyproject.toml),
and [npm metadata](https://github.com/DeusData/codebase-memory-mcp/blob/v0.9.0/pkg/npm/package.json)
still say `0.8.1`. A checksum-pinned release archive is more deterministic
until the distribution channels demonstrably move in lockstep.

## Capability disposition

| Required exploration promise | CBM disposition | Toolkit requirement |
| --- | --- | --- |
| Ranked repository orientation, symbols, signatures, callers, reverse dependencies, and source snippets | Replace | Fixture tests must cover ambiguous names, nested symbols, changed source, pagination, and bounded output. |
| Exact/heuristic reference distinction and boundary-stating no-match output | Replace the query engine; retain the epistemic rule | Every negative or exhaustive claim must check index coverage and relevant pagination, then verify excluded, skipped, or unparsed paths with direct source search. |
| Lazy freshness on every query | Replace | Gate graph use on project identity, generation/status, and targeted coverage. Test an uncommitted edit before and after watcher synchronization. |
| Named live/dead policy zones | No documented equivalent | Dropped. A filtered or partial answer must state its coverage boundary. |
| Committed symbol-anchored notes with deterministic re-anchoring | No documented equivalent; ADRs are not a substitute | Dropped without migration or a companion implementation. Durable rationale stays in normal design/contributor docs. |
| Direct enclosing-symbol lookup from a file position | No documented direct equivalent | Dropped. Resolve the relevant qualified symbol through graph/source search instead of maintaining a second syntax index. |
| Local/offline operation | Upstream-supported | Verify cache permissions, cleanup, allowed-root enforcement, ignore behavior, and no network dependency after installation. |

## Local migration surface

The canonical live contract is `.claude/skills/codebase-memory/SKILL.md`,
with generated regular-file plugin entrypoints. Always-on routing and
delegation behavior also appears in:

- `.claude/rules/token-discipline.md` and `quality-discipline.md`;
- `.claude/agents/scout.md` and `critic.md`;
- the build, breakdown, onboard, work, and clone-audit skills;
- Claude Code, Codex, and Antigravity runtime guides and installers;
- `agentic audit` and `agentprof` usage attribution;
- Codebase-Memory integration, live-smoke, and exact retirement tests; and
- checksum-pinned release metadata plus the project-scoping launcher.

Several live files in this surface already contain user changes. The
implementation must read and merge each one rather than replacing it from a
prepared copy.

## Adopted cutover

The maintainer selected an atomic hard cutover:

1. checksum-pin and install only the headless binary plus toolkit launcher;
2. bundle schema-specific Claude Code and Codex MCP declarations and document
   Antigravity's native registration;
3. replace the canonical skill, routing, telemetry, audit semantics, and
   evals;
4. drop unsupported notes, zones, and position-lookup contracts; and
5. remove the former implementation and its dedicated current-tree artifacts.

The shared CBM cache is never deleted automatically, so uninstalling or
rolling back package configuration does not destroy user indexes. No
compatibility backend, temporary dual-routing period, or historical artifact
tree remains in the current checkout.

## Decisions

All adoption decisions are closed by
`specs/codebase-memory-hard-cutover/SPEC.md`.
