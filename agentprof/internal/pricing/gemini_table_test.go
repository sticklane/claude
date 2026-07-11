package pricing

import "testing"

func TestPriceGeminiFlashMediumMixedUsage(t *testing.T) {
	// Gemini Flash rate card (gemini-2.5-flash), per Google's published
	// Gemini API pricing: $0.30/MTok input, $2.50/MTok output (incl.
	// thinking tokens), $0.03/MTok cached input. See
	// testdata/gemini_pricing.json for the sourced figures and provenance.
	// 1_000_000*0.30 + 100_000*2.50 + 200_000*0.03 =
	// 300_000 + 250_000 + 6_000 = 556_000 microusd.
	got, priced := PriceGemini("Gemini 3.5 Flash (Medium)", Usage{
		InputTokens:     1_000_000,
		OutputTokens:    100_000,
		CacheReadTokens: 200_000,
	})
	if !priced {
		t.Fatal("expected priced=true for mapped Gemini display string")
	}
	if got != 556_000 {
		t.Errorf("got %d microusd, want 556000", got)
	}
}

func TestPriceGeminiRoundsHalfAwayFromZero(t *testing.T) {
	// 1 output token = 2.5 microusd ($2.50/MTok), rounds half away from
	// zero to 3 — mirroring Price's rounding convention.
	got, priced := PriceGemini("Gemini 3.5 Flash (Medium)", Usage{OutputTokens: 1})
	if !priced {
		t.Fatal("expected priced=true")
	}
	if got != 3 {
		t.Errorf("got %d microusd, want 3 (2.5 rounded half away from zero)", got)
	}
}

func TestPriceGeminiUnmappedDisplayStringReturnsUnpriced(t *testing.T) {
	// An unmapped display string is not priced — same convention as Price:
	// (0, false), so no cost_microusd is emitted for that sample.
	got, priced := PriceGemini("Gemini Unknown Model", Usage{
		InputTokens:  1_000_000,
		OutputTokens: 1_000_000,
	})
	if priced {
		t.Error("expected priced=false for unmapped Gemini display string")
	}
	if got != 0 {
		t.Errorf("got %d microusd, want 0 for unmapped display string", got)
	}
}
