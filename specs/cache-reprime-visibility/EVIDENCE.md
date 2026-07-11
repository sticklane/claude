# Evidence: cache re-prime cost, 2026-06-27 → 2026-07-11

Source: `agentprof claude --days 14` run 2026-07-11 (window ≈ 2026-06-27 →
2026-07-11), analyzed with ad-hoc scripts over the JSONL output. Raw
profile/JSONL intentionally NOT pinned in-repo (large; and raw frames may
carry text that doesn't belong in a repo — see the frame-denylist
requirement in specs/agentprof-attribution-gaps). Regenerate with:

    cd agentprof && ./agentprof claude --since 2026-06-27T00:00:00Z -o /tmp/win.jsonl --summary /tmp/summary.json

## Headline numbers

- Window totals: $9,195, 295 sessions, 94,182 samples, 79,790 calls.
- Cache dominates: for fable-5 spend, ~46% cache reads + ~41% cache writes
  vs ~10% output tokens (in-equivalent-token estimate).
- **Re-primes: 915 samples with cache_write_tokens > 60k** — 155 MTok of
  the window's 409 MTok total cache writes; bundled sample cost ~$1,713.
  Largest single write: 671k tokens ($2.54) on turn "t14 · how are we
  doing?" (claude repo). Pattern: turn lands after cache TTL expiry on a
  long-lived session; the whole accumulated context re-writes at 1.25×.
- Session-length tail: median 2 turns/session (good), p90 = 7, max = 18;
  23 sessions ran ≥8 turns. Top-15 sessions by cost = $2,900 (32% of all
  spend), each 972–2,574 calls.
- Average main-loop context per call: claude repo 319k tokens(!),
  fooszone 188k, home-dir sessions 181k, hub 178k.
- Cache-write churn outliers (cw/cr ratio > 0.15 at >$20): 4 sessions,
  worst $241 at ratio 0.20.

## Method notes

- "Re-prime" heuristic: `cache_write_tokens > 60k` on any sample; the spec
  refines this to "not the session's first model call, write > 50k".
- The bundled $1,713 is the full cost of those samples (includes their
  output/input), dominated by the cache-write component.
- Top single re-prime turns observed: 671k/610k (claude, session
  e2990586), 561k (claude eed20d5f), 559k (fooszone 8889d425), 554k
  (fooszone 53177041) — all main-loop, all mid-session turn starts.
