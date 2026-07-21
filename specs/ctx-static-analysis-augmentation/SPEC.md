# ctx: augment with traditional static analysis (exact refs, structural search, clone detection)

Breakdown-ready: false — two decision forks below need /design (or a
maintainer call) before breakdown.

## Problem

`ctx` answers structure questions from tree-sitter name-matching, and
every `refs`/`sig` result is tagged `heuristic`. That is the right
build-time architecture (per-file isolation, no compiler in the loop —
research doc decision), but at query time it leaves three gaps that
traditional static analysis already solves:

1. **Precision.** Heuristic refs cannot distinguish two same-named
   symbols; live case (fooszone, 2026-07-20): `main.rodSpecs` defined in
   both `go/cmd/mlhybrid` and `attic/go-cmd/mloverlay` — `ctx sig` is
   permanently ambiguous, and a rename/impact question over such a symbol
   gets wrong counts. LSP servers (gopls, typescript-language-server)
   give compiler-verified definitions/references, and LSP 3.17 adds call
   and type hierarchy. Serena-style agent layers demonstrate the pattern
   of LSP-as-symbol-backend for agents.
2. **Structural content search.** The sanctioned fallback for
   body/literal/pattern questions is plain Grep, which is precision-poor
   and token-noisy. ast-grep (tree-sitter-based, same grammar stack ctx
   already ships) answers "find this code shape" with far fewer false
   positives than regex.
3. **Duplication discovery.** Nothing in the toolkit finds clones. The
   same fooszone session hand-discovered three independent TS homography
   implementations and repeated Go CLI helpers (`drawLine` ×3,
   `writeJSON` ×2, hardcoded rod specs duplicating
   `go/internal/tablespec`) — exactly what clone detectors (jscpd,
   PMD CPD, Go `dupl`) emit mechanically at zero model cost.

## Solution

Augment, don't absorb: keep the ctx core model-free and per-file
(architecture rules unchanged), and add static-analysis power at two
levels — (a) doctrine: the ctx skill and harness-audit adopt existing
CLIs (ast-grep, clone detector) as named rungs/stages; (b) integration:
an opt-in `--exact` path that consults a language server when one is
available, falling back to heuristic results identically otherwise.
Diagnostics-class tools (tsc, go vet, staticcheck, eslint) explicitly
stay in `check.sh`/gates — they answer "is it correct", not "what is the
structure", and must not creep into ctx.

## Decision forks (need /design)

- F1 — Exact-refs delivery: (i) `ctx refs --exact` shells out to an LSP
  client helper per language when a server binary is found (cached in the
  index with a generation stamp), vs (ii) doctrine-only — the skill
  teaches reaching for an LSP-capable tool (e.g. Serena MCP, `gopls`
  CLI) directly, ctx untouched. (i) is one UX and one cache; (ii) is
  zero Rust work but N per-language recipes. Evaluate against
  agent-buildability and maintenance cost.
- F2 — Clone detection home: (i) `ctx dupes` wrapping a bundled
  detector, (ii) a harness-audit stage invoking jscpd/dupl per stack,
  or (iii) a standalone repo-audit skill. Leans (ii): audits are already
  the periodic, read-only reporting surface, and clone output is a
  report, not a query.

## Requirements

- R1 — ast-grep as the structural-search rung. The ctx skill's reading
  ladder (specs/ctx-skill-token-doctrine R2) names ast-grep as the
  preferred content-search fallback when installed, with one worked
  example per major language family, and Grep as the fallback's
  fallback. Acceptance: skill body contains an `ast-grep --pattern`
  example and the precedence statement.
- R2 — Exact refs per F1's decision. Whichever fork wins: given a repo
  with gopls or typescript-language-server available, an
  exact-references path exists and its results drop the `heuristic` tag
  (or are documented as compiler-verified); with no server installed,
  behavior is byte-identical to today. Acceptance: golden test or
  documented recipe run against the `main.rodSpecs`-style ambiguity
  reproduces a disambiguated answer.
- R3 — Clone detection per F2's decision. A supported, documented way to
  get a clone report for a mixed TS/Go repo, surfaced where F2 decides;
  run against fooszone it must rediscover the three-homography cluster
  (src/video/homography.ts, src/annotator/components/Canvas.tsx,
  src/viewer/possessionAnalyzer.ts). Acceptance: that named cluster
  appears in the report output.
- R4 — Boundary statement. ctx docs and skill state the division:
  structure queries (ctx) / structural content search (ast-grep) /
  exactness on demand (LSP path) / correctness diagnostics (check.sh
  gates, never ctx). Acceptance: statement present in both the skill and
  context-tree/ docs.
- R5 — Index-membership hygiene is out of scope here: committed
  vendored/generated trees polluting `map` (fooszone: root
  `paper-full.min.js`, `attic/`) is owned by specs/ctxignore-git-overlay;
  this spec must not add a second exclusion mechanism.

## Evidence / prior art

- Live ambiguity + duplication cases: fooszone session 2026-07-20
  (memory: `feedback-ctx-skill-triggering.md`; homography/rod-spec
  findings reported to Steven same day).
- LSP for agents, call/type hierarchy in LSP 3.17; Serena as LSP-backed
  symbol layer: https://lsp-client.github.io/ ,
  https://rywalker.com/research/code-intelligence-tools
- Tree-sitter knowledge-graph token economics (10× fewer tokens at
  83% vs 92% quality — motivates keeping an exactness escalation path):
  https://arxiv.org/html/2603.27277v1
