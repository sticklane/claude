package pricing

import "testing"

func i64(v int64) *int64 { return &v }

func TestPriceFable5MixedUsage(t *testing.T) {
	// $10 in, $50 out, $1 cache read, $12.50 5m write per MTok.
	// 1000*10 + 2000*50 + 30000*1 + 5000*12.5 =
	// 10_000 + 100_000 + 30_000 + 62_500 = 202_500 microusd.
	got, priced := Price("claude-fable-5-20260101", Usage{
		InputTokens:         1000,
		OutputTokens:        2000,
		CacheReadTokens:     30000,
		CacheCreationTokens: 5000,
	})
	if !priced {
		t.Fatal("expected priced=true for claude-fable-5 prefix")
	}
	if got != 202500 {
		t.Errorf("got %d microusd, want 202500", got)
	}
}

func TestPriceOpus4ModernRates(t *testing.T) {
	// Opus 4.5+ rates: $5 in, $25 out, $0.50 cache read per MTok.
	// 1_000_000*5 + 100_000*25 + 200_000*0.5 =
	// 5_000_000 + 2_500_000 + 100_000 = 7_600_000 microusd.
	got, priced := Price("claude-opus-4-6", Usage{
		InputTokens:     1_000_000,
		OutputTokens:    100_000,
		CacheReadTokens: 200_000,
	})
	if !priced {
		t.Fatal("expected priced=true for claude-opus-4 prefix")
	}
	if got != 7_600_000 {
		t.Errorf("got %d microusd, want 7600000", got)
	}
}

func TestPriceLongestPrefixWinsForLegacyOpus41(t *testing.T) {
	// claude-opus-4-1-20250805 matches both claude-opus-4-1 (legacy,
	// $15/MTok input) and claude-opus-4 ($5/MTok input). The longer,
	// more specific prefix must win: 1_000_000*15 = 15_000_000 microusd.
	got, priced := Price("claude-opus-4-1-20250805", Usage{InputTokens: 1_000_000})
	if !priced {
		t.Fatal("expected priced=true for claude-opus-4-1 prefix")
	}
	if got != 15_000_000 {
		t.Errorf("got %d microusd, want 15000000 (legacy Opus 4.1 rate)", got)
	}
}

func TestPriceSonnetMixedUsage(t *testing.T) {
	// $3 in, $15 out per MTok.
	// 500_000*3 + 100_000*15 = 1_500_000 + 1_500_000 = 3_000_000 microusd.
	got, priced := Price("claude-sonnet-4-5-20250929", Usage{
		InputTokens:  500_000,
		OutputTokens: 100_000,
	})
	if !priced {
		t.Fatal("expected priced=true for claude-sonnet- prefix")
	}
	if got != 3_000_000 {
		t.Errorf("got %d microusd, want 3000000", got)
	}
}

func TestPriceHaikuMixedUsage(t *testing.T) {
	// $1 in, $5 out per MTok.
	// 2_000_000*1 + 400_000*5 = 2_000_000 + 2_000_000 = 4_000_000 microusd.
	got, priced := Price("claude-haiku-4-5", Usage{
		InputTokens:  2_000_000,
		OutputTokens: 400_000,
	})
	if !priced {
		t.Fatal("expected priced=true for claude-haiku- prefix")
	}
	if got != 4_000_000 {
		t.Errorf("got %d microusd, want 4000000", got)
	}
}

func TestPriceCacheCreationSubfieldsSplit5mAnd1h(t *testing.T) {
	// Fable 5: 5m write $12.50/MTok, 1h write $20/MTok.
	// 10_000*12.5 + 20_000*20 = 125_000 + 400_000 = 525_000 microusd.
	// CacheCreationTokens must be ignored when sub-fields are present
	// (30_000 at the 5m rate would instead give 375_000).
	got, priced := Price("claude-fable-5", Usage{
		CacheCreationTokens: 30_000,
		Cache5mTokens:       i64(10_000),
		Cache1hTokens:       i64(20_000),
	})
	if !priced {
		t.Fatal("expected priced=true")
	}
	if got != 525_000 {
		t.Errorf("got %d microusd, want 525000", got)
	}
}

func TestPriceCacheCreationWithoutSubfieldsUses5mRate(t *testing.T) {
	// Fable 5: 30_000 cache-creation tokens at the 5m rate ($12.50/MTok)
	// = 375_000 microusd.
	got, priced := Price("claude-fable-5", Usage{CacheCreationTokens: 30_000})
	if !priced {
		t.Fatal("expected priced=true")
	}
	if got != 375_000 {
		t.Errorf("got %d microusd, want 375000", got)
	}
}

func TestPriceOnlyOneCacheCreationSubfieldPresent(t *testing.T) {
	// A present 1h sub-field alone still switches to sub-field pricing:
	// 5_000*20 = 100_000 microusd; CacheCreationTokens ignored.
	got, priced := Price("claude-fable-5", Usage{
		CacheCreationTokens: 30_000,
		Cache1hTokens:       i64(5_000),
	})
	if !priced {
		t.Fatal("expected priced=true")
	}
	if got != 100_000 {
		t.Errorf("got %d microusd, want 100000", got)
	}
}

func TestPriceRoundsHalfAwayFromZero(t *testing.T) {
	// 1 fable 5m-write token = 12.5 microusd, rounds half-away to 13.
	got, priced := Price("claude-fable-5", Usage{Cache5mTokens: i64(1)})
	if !priced {
		t.Fatal("expected priced=true")
	}
	if got != 13 {
		t.Errorf("got %d microusd, want 13 (12.5 rounded half away from zero)", got)
	}
}

func TestPriceRoundsFractionsBelowHalfDown(t *testing.T) {
	// 4 haiku cache-read tokens = 0.4 microusd, rounds to 0.
	got, priced := Price("claude-haiku-4-5", Usage{CacheReadTokens: 4})
	if !priced {
		t.Fatal("expected priced=true")
	}
	if got != 0 {
		t.Errorf("got %d microusd, want 0 (0.4 rounds down)", got)
	}
}

func TestPriceUnknownModelReturnsZeroUnpriced(t *testing.T) {
	got, priced := Price("gpt-4o", Usage{InputTokens: 1_000_000, OutputTokens: 1_000_000})
	if priced {
		t.Error("expected priced=false for unknown model")
	}
	if got != 0 {
		t.Errorf("got %d microusd, want 0 for unknown model", got)
	}
}

func TestPriceSyntheticModelReturnsZeroUnpriced(t *testing.T) {
	got, priced := Price("<synthetic>", Usage{InputTokens: 1_000_000})
	if priced {
		t.Error("expected priced=false for <synthetic>")
	}
	if got != 0 {
		t.Errorf("got %d microusd, want 0 for <synthetic>", got)
	}
}
