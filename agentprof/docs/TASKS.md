# Tech debt / future tasks

- **Dead branch in `otel.AddJSON` fast path** — `internal/otel/otel.go` ~L279/291:
  `out` is never nil (allocated with positive cap, empty-spans case returns
  earlier), so the `if out == nil { return data, nil }` early-return is
  unreachable; when every span fails hex-decode we fall through and copy `data`
  verbatim — correct output, one avoidable allocation. Drop the nil check or
  gate on a `wrote bool`. (Critic finding, 2026-07-05, non-blocking.)

- **Wake-budget hook has no failure side channel** —
  `hooks/session-refresh/refresh-check.sh` silently no-ops when the agentprof
  binary, `jq`, or the 7d summary is missing (correct: never block a session),
  but nothing records that it fired empty. If the refresh launchd job dies,
  wake-budget enforcement vanishes machine-wide with zero trace. Add a
  one-line append to a log under `~/Library/Logs/agentprof-refresh/` on each
  silent-skip path so the outage is at least discoverable. (Log-review
  finding, 2026-07-15.)

- **Parser drops are silent** — `internal/claude/claude.go:326-329` discards
  subagent sidecar dirs with no resolvable owning project with no counter or
  stderr note, and the skill-attribution fallback (`attributionSkill` →
  `/<command-name>` tag) fires unlogged. Emit per-run drop/fallback counts on
  stderr (the refresh log now has timestamped run markers to attribute them
  to). (Log-review finding, 2026-07-15.)

Recently closed (specs archived under `specs/archive/`):

- **Shared file-adapter runner** — `runFileAdapter` extracted for gcp + vertex;
  otel left bespoke. `specs/archive/adapter-file-runner/`.
- **`otel.AddJSON` triple parse** — replaced with single-pass decoder-offset
  splice (protojson once, no `json.Marshal`). Time −5.7%, memory (B/op) −34% on a
  large-body gen_ai batch; alloc *count* rose ~50% (delimiter boxing from
  `json.Decoder.Token()`) — accepted, allocs are tiny. `specs/archive/otel-addjson-fastpath/`.
