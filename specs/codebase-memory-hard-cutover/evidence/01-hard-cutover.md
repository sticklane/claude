# Independent verification: Task 01 hard cutover

Verdict: **PASS**

Verified the final refreshed uncommitted snapshot in the isolated copy at
`/var/folders/nf/mv6wh32s01s9tnlxc1cfrg_c0000gn/T/tmp.Ptq5ZxI00X/repo`
against base `aea89bd0f93660bca0cb9915a14c7f6df4ef6dc8`.

No branch was given, so worktree integrity against a named branch was not
checked. I staged all files only in the isolated copy and confirmed a nonempty
diff: 478 files changed, 6,235 insertions, and 37,633 deletions.

Canonical scope came from `bd show agentic-nes --json`, not the frozen-display
task header. It includes both `scripts/**` and `.agents/**`, with notes tying
them to manual network-smoke inventory, frozen-surface retirement, and
repo-local Codex skill discovery.

## Findings

No blocking findings.

The final code-review repairs were verified:

- `.agents/skills/ctx` is absent and listed in the exact retirement manifest.
  `.agents/skills/codebase-memory` resolves to the canonical
  `.claude/skills/codebase-memory` directory.
- The absence check detects the bare product token, explicit product paths,
  untracked non-ignored content, and broken symlinks at retirement targets.
  Generic programming uses of `ctx` are confined to an exact, stale-checked
  allowlist whose entries may not contain product patterns.
- Active docs and retained specs no longer carry non-allowlisted ctx product
  references.
- The skill describes v0.9.0 `trace_path` as a single
  `function_name` traversal with `direction`, `depth`, and `mode`, rather than
  a source-to-target relationship query.
- Audit and agentprof require Codebase-Memory identity around MCP query names;
  a generic tool named `search_code` does not count. Both recognize absolute
  launcher paths.
- Canonical Beads scope now includes `.agents/**`; no cutover-owned path remains
  outside the live Touch set.

## Acceptance command evidence

1. ✓ `bash tests/test_codebase_memory_integration.sh`

   ```text
   launcher: .../success/agentic-codebase-memory-mcp
   cache: ${XDG_CACHE_HOME:-$HOME/.cache}/agentic/codebase-memory
   The upstream client-configuring installer was not run.
   test_codebase_memory_integration: PASS
   ```

2. ✓ `bash tests/test_no_ctx_surface.sh`

   ```text
   test_no_ctx_surface: PASS
   ```

3. ✓ `bash tests/test_codebase_memory_live.sh`

   ```text
   level=info msg=mem.init budget_mb=4096 total_ram_mb=16384
   level=info msg=index.supervisor.reap outcome=clean exit_code=0 signal=0
   test_codebase_memory_live: PASS (darwin-arm64 0.9.0, project=private-var-folders-...)
   ```

   This was a real networked run of the repository-pinned v0.9.0 Darwin arm64
   archive. The script verified the archive digest, indexed a temporary Git
   fixture, and completed `get_architecture`, `get_graph_schema`,
   `search_graph`, and `get_code_snippet` using temporary binary and cache
   roots. Its checkout-status comparison remained unchanged.

4. ✓ `bash agentprof/scripts/check.sh`

   ```text
   check: format-check ok
   check: lint ok
   check: tests ok
   ```

5. ✓ `python3 -m pytest -q tests/test_agentic_audit.py tests/test_agentic_cli_retirement.py`

   ```text
   .................                                                        [100%]
   17 passed in 19.63s
   ```

6. ✓ `bash tests/test_codex_skill_entrypoints.sh`

   ```text
   trajectory: Codex drain rolling events verified
   CODEX SKILLS OK
   ```

   The prior orphaned/broken ctx diagnostic is gone. The canonical
   Codebase-Memory symlink and generated regular-file package entrypoint both
   resolve correctly.

7. ✓ `python3 ~/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py .`

   ```text
   Plugin validation passed: .../repo
   ```

8. ✓ `claude plugin validate .`

   ```text
   Validating marketplace manifest: .../.claude-plugin/marketplace.json
   ✔ Validation passed
   ```

9. ✓ `agy plugin validate .`

   ```text
   [ok] .
   ✔ skills : 29 processed
   - mcpServers : skipped (not found)
   ```

   Antigravity's intentionally minimal manifest remains schema-valid; native
   MCP registration is documentation-owned.

10. ✓ `rg -n -A8 '^## Antigravity registration$' antigravity/README.md | rg -q '/mcp|mcp_config\\.json'`

    Exit 0. Manual inspection confirms the section names
    `codebase-memory-mcp`, the `agentic-codebase-memory-mcp` launcher, native
    `/mcp`, and `~/.gemini/config/mcp_config.json`, and warns against
    substituting a Claude or Codex command.

11. ✓ `bash scripts/check.sh`

    ```text
    [ok] tests/test_runtime_gate_adapters.sh
    [ok] tests/test_verifier_worktree_integrity.sh
    == pytest tests ==
    [ok] tests/test_agentic_audit.py
    [ok] tests/test_agentic_cli_retirement.py
    ...
    == manual (inventoried, run explicitly) ==
    - tests/test_codebase_memory_live.sh — Downloads and executes the pinned upstream release; run explicitly as the supported-host smoke test.
    check.sh: green
    ```

    One authoritative canonical run completed normally. Its long interval was
    in the expected `tests/test_agentic_latency.sh` case, which finished green
    within the configured per-test timeout.

## Requirement adequacy

- **R1 — adequate, L2.** The integration test exercises all four platform
  selections, production rejection of test overrides, network-free dry run,
  unsupported-platform rejection, successful replacement, checksum and
  extraction preservation, forced second-move rollback, Git-root isolation,
  cache selection, argument forwarding, and non-Git refusal. The release pin
  contains explicit assets and digests.
- **R2 — adequate, L2.** Isolated package assertions prove the Claude wrapped
  `.mcp.json` and Codex inline `mcpServers` shapes, exact server key, command,
  arguments, and Claude root environment. Both package validators pass.
  Antigravity remains schema-minimal and documents its native registration.
- **R3 — adequate, L1/L2.** The canonical and repo-local Codex skills use the
  pinned tool surface, corrected `trace_path` semantics, progressive query
  ladder, and project/freshness/pagination/coverage safeguards. Each
  deterministic edge case is checked within its named local recipe; generated
  package entrypoints are current.
- **R4 — adequate, L1/L2.** The exact routing manifest is exercised for
  CBM-first, bounded fallback, parent handoff, telemetry, and
  Antigravity-native clauses. Manual review confirms child frontmatter does not
  invent MCP grants and instead consumes parent-distilled project, symbol,
  path, index, and coverage evidence.
- **R5 — adequate, L3.** Agentprof format/vet/tests exercise exact MCP
  identity, relative and absolute CLI launch, canonical skill usage, and
  generic-name rejection. Seventeen audit/CLI tests exercise those identity
  boundaries, ordering, date filtering, read-only dry run, tracker filing, and
  dedup.
- **R6 — adequate, L2.** The exact retirement manifest includes all three old
  skill surfaces, including the repo-local broken symlink. Every target is
  absent; bare product references across current tracked/untracked content are
  bounded by explicit current/historical and generic-context allowlists.
  Durable preflight evidence records dirty-path ownership decisions.
- **R7 — adequate, L1-L3.** Deterministic installer, rollback, launcher,
  packaging, routing, skill, telemetry, retirement, symlink, and inventory
  tests pass; package validators pass; the networked four-query smoke is L3;
  and the canonical gate is green while correctly inventorying the smoke as
  manual.

## Scope, append-only, hard-removal, and overfitting review

- `config/ctx-retirement-paths.txt` covers the implementation, repository
  cache, canonical/repo-local/generated old skills, evals, capability test,
  old research/guides, twelve ctx spec families, and ctx-only artifacts in
  retained families. Every target is absent.
- Retained task-file changes remove incoming product references from active
  definitions and evidence; deleted task files are exact retirement targets.
  These changes are required by R6's immediate current-tree retirement. No
  unrelated task-definition change was found.
- Current Beads scope covers every cutover-owned path, including
  `.agents/**` and `scripts/**`. Remaining base-diff paths outside that scope
  concern pre-existing Beads exports, agent-console, hooks/templates, and the
  root Antigravity manifest. Their contents are unrelated to the conversion
  and were not attributed to this task.
- The absence allowlist is exact and self-checking: a missing entry, stale
  generic entry, product token in a generic entry, or remaining retirement
  symlink fails. The telemetry fixtures pair true CBM identities with generic
  near-misses. No exact-input special case or vacuous pass was found.
- The pinned upstream v0.9.0 documentation was independently checked for
  `trace_path(function_name=..., direction=...)`, depth-bounded traversal, and
  the remaining live query names. The skill and smoke agree with that surface.
