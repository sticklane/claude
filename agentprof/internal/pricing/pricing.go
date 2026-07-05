// Package pricing computes the cost of a Claude API message from its token
// usage, using a built-in table of per-MTok rates keyed by model-id prefix.
// Pure functions, no I/O.
package pricing

import "math"

// Usage carries the token counts of one message.usage block.
// Cache5mTokens and Cache1hTokens mirror the optional
// message.usage.cache_creation sub-fields (ephemeral_5m_input_tokens /
// ephemeral_1h_input_tokens); nil means the field was absent.
type Usage struct {
	InputTokens         int64
	OutputTokens        int64
	CacheReadTokens     int64
	CacheCreationTokens int64
	Cache5mTokens       *int64
	Cache1hTokens       *int64
}

// Price returns the message cost in micro-USD, cost_microusd =
// round(dollars * 1e6) with ties rounded away from zero. Unrecognized
// models (including "<synthetic>") return (0, false).
//
// If either cache_creation sub-field is present, 5m and 1h write tokens are
// priced at their respective rates and CacheCreationTokens is ignored;
// otherwise CacheCreationTokens is priced entirely at the 5m rate.
func Price(model string, u Usage) (microusd int64, priced bool) {
	r, ok := lookup(model)
	if !ok {
		return 0, false
	}
	// Rates are micro-USD per token (see the rates type in table.go).
	micro := float64(u.InputTokens)*r.Input +
		float64(u.OutputTokens)*r.Output +
		float64(u.CacheReadTokens)*r.CacheRead
	if u.Cache5mTokens != nil || u.Cache1hTokens != nil {
		if u.Cache5mTokens != nil {
			micro += float64(*u.Cache5mTokens) * r.CacheWrite5m
		}
		if u.Cache1hTokens != nil {
			micro += float64(*u.Cache1hTokens) * r.CacheWrite1h
		}
	} else {
		micro += float64(u.CacheCreationTokens) * r.CacheWrite5m
	}
	return int64(math.Round(micro)), true
}
