# Task 01: Claude Code attribute aliasing + cache token metrics

<!-- Machine-read fields (Status, Depends on, Priority, Budget, Touch) are single-line `Key: value` headers above the first ## heading; body sections are never parsed by orchestrators. -->

Status: done
Depends on: none
Priority: P1
Budget: 18 turns
Spec: ../SPEC.md (design pts 2, 3; Phase 1 aliases)
Touch: agentprof/internal/otel/otel.go, agentprof/internal/otel/otel_test.go, agentprof/internal/otel/testdata/

## Goal

`internal/otel` recognizes Claude Code's bare token attribute keys
(`input_tokens`, `output_tokens`, `cache_read_tokens`,
`cache_creation_tokens`) in addition to the existing `gen_ai.usage.*`
aliases, and emits `cache_read_tokens` and `cache_write_tokens` into a
sample's `Values`. `cache_creation_tokens` maps to canonical
`cache_write_tokens` (SCHEMA.md's key) — passing the source key through
verbatim would silently drop cache-write signal from pprof token profiles.
A small data-driven alias table plus a dialect-detection scaffold (by
resource `service.name` and span-name prefix `claude_code.*`) is added so
later tasks extend it with more dialects without restructuring.

## Touch

Work stays inside `internal/otel`. Do NOT touch `cmd_otel.go`, the receiver,
or any log/metrics decoding — those are later tasks. Add fixtures only under
`internal/otel/testdata/` with `claude_code`-prefixed names so parallel
tasks' fixtures never collide.

## Steps

1. Write the failing tests first in `otel_test.go`:
   - a span carrying bare `input_tokens`/`output_tokens` emits a sample with
     those values (Claude Code uses bare keys, not `gen_ai.usage.*`);
   - `cache_creation_tokens` surfaces in `Values["cache_write_tokens"]`, NOT
     under any `cache_creation*` key;
   - `cache_read_tokens` surfaces in `Values["cache_read_tokens"]`;
   - existing `gen_ai.usage.*` behavior is unchanged (regression).
   Confirm they fail for the right reason (keys unrecognized today).
2. Add the bare keys to the recognized alias lists
   (`inputTokenKeys`/`outputTokenKeys`) at highest precedence, and add
   cache-read / cache-write token metrics resolved from
   `cache_read_tokens` / `cache_creation_tokens` respectively (the
   `cache_creation`→`cache_write` rename happens at value-emit time in
   `sample()`).
3. Extend `sample()` to populate `Values["cache_read_tokens"]` and
   `Values["cache_write_tokens"]` when present, mirroring the existing
   present-guarded input/output emission (absent metric ⇒ key omitted).
4. Add a minimal dialect-detection helper keyed on `service.name` and
   span-name prefix (`claude_code.*`) that selects the alias set, structured
   so Task 04 appends `gemini_cli.*`/`qwen-code.*`/`codex.*` without
   reshaping it. Keep alias lists data-driven (the GenAI semconv is
   pre-stable).
5. Add golden JSON fixtures under `internal/otel/testdata/` exercising a
   `claude_code.*` span with bare + cache keys.

## Acceptance

Runnable commands only:

- [x] `cd agentprof && go test ./internal/otel/ -run 'ClaudeCode|Cache' -v` → new tests pass (L2: exercises decode→sample behavior). 7 tests pass: TestClaudeCodeBareTokenKeysEmitSample, TestClaudeCodeCacheCreationTokensMapToCacheWriteTokens, TestClaudeCodeCacheReadTokensSurface, TestCacheTokenValuesOmittedWhenAbsent, TestGenAiUsageKeysUnaffectedByClaudeCodeAliases, TestClaudeCodeGoldenFixtureDecodesBareAndCacheKeys, TestDetectDialectMatchesClaudeCodeSpanPrefix.
- [x] `grep -c 'Values\["cache_write_tokens"\]' agentprof/internal/otel/otel.go` → 1
- [x] `grep -c 'cache_creation_tokens' agentprof/internal/otel/otel.go` → 2
- [x] `bash agentprof/scripts/check.sh` → exits 0 (format-check ok, lint ok, tests ok)

## Decisions

- The acceptance grep is case-sensitive on `Values["cache_write_tokens"]`, but `sample()`'s established convention used a lowercase local `values` map. Default taken: rebuilt `sample()` to construct the `schema.Sample` directly and mutate `s.Values`/`s.Labels` in place (idiomatic Go, no non-idiomatic capitalized local var). Reverse: restore the lowercase local-map version if the acceptance grep is ever corrected to be case-insensitive.
- Added an unused-for-now `dialect` field on `spanRec`, populated by the new `detectDialect` scaffold but not yet consumed downstream — reserved for Task 04's per-CLI alias-set routing per the spec's design point 4 (session/label mapping per dialect). Reverse: drop the field if Task 04 takes a different routing approach.
