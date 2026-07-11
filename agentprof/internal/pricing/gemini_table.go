package pricing

import "math"

// geminiRates holds per-MTok USD prices for a Gemini model. As with the
// Claude `rates` type in table.go, a dollars-per-MTok figure is numerically
// identical to micro-USD per token, which is what PriceGemini sums over.
//
// Gemini's rate card has no separate cache-write (5m/1h) tiers like
// Anthropic's; its cached content is billed as a discounted cached-input
// read plus a time-based storage-per-hour charge that is not modeled here.
// So PriceGemini prices input, output, and cache-read tokens only.
type geminiRates struct {
	Input     float64 // USD per MTok
	Output    float64 // USD per MTok (Gemini 2.5 Flash output price includes thinking tokens)
	CacheRead float64 // USD per MTok (cached input)
}

// geminiTable maps the exact human-readable model display strings observed in
// Antigravity's gen_metadata field 21 to a Gemini rate row. Source of truth:
// Google's published Gemini API pricing,
// https://ai.google.dev/gemini-api/docs/pricing (fetched 2026-07-11); see
// internal/pricing/testdata/gemini_pricing.json for the sourced figures and
// provenance.
//
// The observed display string "Gemini 3.5 Flash (Medium)" is priced against
// Google's published Gemini Flash rate card (gemini-2.5-flash, the current
// published Flash model) as the closest published pricing for the Flash
// family. Unlike the Claude table this is an EXACT-match map, not a prefix
// scan: the display string is not a stable model id, so only strings we have
// explicitly mapped are priced (Solution item 3 does not require prefix
// matching).
var geminiTable = map[string]geminiRates{
	"Gemini 3.5 Flash (Medium)": {Input: 0.30, Output: 2.50, CacheRead: 0.03},
}

// PriceGemini returns the message cost in micro-USD for a Gemini model
// identified by its raw display string (Antigravity gen_metadata field 21),
// mirroring Price's rounding (round half away from zero) and its priced
// convention: an unmapped display string returns (0, false) so no
// cost_microusd is emitted for that sample.
func PriceGemini(displayName string, u Usage) (microusd int64, priced bool) {
	r, ok := geminiTable[displayName]
	if !ok {
		return 0, false
	}
	// Rates are micro-USD per token (see geminiRates).
	micro := float64(u.InputTokens)*r.Input +
		float64(u.OutputTokens)*r.Output +
		float64(u.CacheReadTokens)*r.CacheRead
	return int64(math.Round(micro)), true
}
