package pricing

import "strings"

// rates holds per-MTok USD prices. A dollars-per-MTok figure is numerically
// identical to micro-USD per token, which is what Price sums over.
type rates struct {
	Input        float64
	Output       float64
	CacheRead    float64
	CacheWrite5m float64
	CacheWrite1h float64
}

// table maps model-id prefixes to rates. Source of truth:
// https://docs.claude.com/en/docs/about-claude/pricing (fetched 2026-07-02).
//
// Match order: entries are scanned top to bottom and the first matching
// prefix wins, so longer / more specific prefixes MUST be listed before
// shorter ones they overlap with (the legacy claude-opus-4-1 and
// claude-opus-4-20250514 entries before claude-opus-4).
//
// Notes:
//   - claude-opus-4 covers Opus 4.5-4.8, all priced identically; the two
//     legacy entries above it carry the old Opus 4 / 4.1 rates.
//   - claude-sonnet- uses standard Sonnet pricing ($3/$15); Sonnet 5's
//     introductory $2/$10 pricing (through 2026-08-31) is not modeled.
//   - claude-haiku- covers Haiku 4.5; Haiku 3.5 uses the old
//     claude-3-5-haiku- naming and does not match (priced=false).
var table = []struct {
	prefix string
	rates  rates
}{
	{"claude-opus-4-1", rates{Input: 15, Output: 75, CacheRead: 1.50, CacheWrite5m: 18.75, CacheWrite1h: 30}},
	{"claude-opus-4-20250514", rates{Input: 15, Output: 75, CacheRead: 1.50, CacheWrite5m: 18.75, CacheWrite1h: 30}},
	{"claude-fable-5", rates{Input: 10, Output: 50, CacheRead: 1, CacheWrite5m: 12.50, CacheWrite1h: 20}},
	{"claude-opus-4", rates{Input: 5, Output: 25, CacheRead: 0.50, CacheWrite5m: 6.25, CacheWrite1h: 10}},
	{"claude-sonnet-", rates{Input: 3, Output: 15, CacheRead: 0.30, CacheWrite5m: 3.75, CacheWrite1h: 6}},
	{"claude-haiku-", rates{Input: 1, Output: 5, CacheRead: 0.10, CacheWrite5m: 1.25, CacheWrite1h: 2}},
}

// lookup returns the rates for the first table entry whose prefix matches
// model, or ok=false for unrecognized models (including "<synthetic>").
func lookup(model string) (rates, bool) {
	for _, e := range table {
		if strings.HasPrefix(model, e.prefix) {
			return e.rates, true
		}
	}
	return rates{}, false
}
