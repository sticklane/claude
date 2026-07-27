# Codebase-Memory live smoke

- Date: 2026-07-26
- Host tuple: `darwin-arm64`
- Release: `v0.9.0`
- Asset: `codebase-memory-mcp-darwin-arm64.tar.gz`
- Verified archive SHA-256:
  `faa02f0404230c451a9812230394481948f80183801fa5bf67044b41c2f25ed4`
- Command: `bash tests/test_codebase_memory_live.sh`
- Result: pass

The test downloaded the repository-pinned release archive, verified the
archive digest before extraction, and installed the binary in a temporary
directory. It initialized a temporary Git fixture and temporary cache, then
successfully exercised:

1. `get_architecture`
2. `get_graph_schema`
3. `search_graph`
4. `get_code_snippet`

The script compared the checkout's Git status before and after the run and
found no change. The temporary fixture, binary, and graph cache were removed
by the test cleanup trap. No user MCP configuration was read or written.
