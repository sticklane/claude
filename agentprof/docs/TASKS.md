# Tech debt / future tasks

- **Dead branch in `otel.AddJSON` fast path** — `internal/otel/otel.go` ~L279/291:
  `out` is never nil (allocated with positive cap, empty-spans case returns
  earlier), so the `if out == nil { return data, nil }` early-return is
  unreachable; when every span fails hex-decode we fall through and copy `data`
  verbatim — correct output, one avoidable allocation. Drop the nil check or
  gate on a `wrote bool`. (Critic finding, 2026-07-05, non-blocking.)

Recently closed (specs archived under `specs/archive/`):

- **Shared file-adapter runner** — `runFileAdapter` extracted for gcp + vertex;
  otel left bespoke. `specs/archive/adapter-file-runner/`.
- **`otel.AddJSON` triple parse** — replaced with single-pass decoder-offset
  splice (protojson once, no `json.Marshal`). Time −5.7%, memory (B/op) −34% on a
  large-body gen_ai batch; alloc *count* rose ~50% (delimiter boxing from
  `json.Decoder.Token()`) — accepted, allocs are tiny. `specs/archive/otel-addjson-fastpath/`.
