package bqtime

import (
	"testing"
	"time"
)

func TestParseAcceptedFormats(t *testing.T) {
	cases := map[string]struct {
		in   string
		want time.Time
	}{
		"space_plain":         {"2026-06-01 09:30:00", time.Date(2026, 6, 1, 9, 30, 0, 0, time.UTC)},
		"space_fractional":    {"2026-06-01 09:30:00.123456", time.Date(2026, 6, 1, 9, 30, 0, 123456000, time.UTC)},
		"space_utc_suffix":    {"2026-06-01 09:30:00 UTC", time.Date(2026, 6, 1, 9, 30, 0, 0, time.UTC)},
		"space_frac_plus_utc": {"2026-06-01 09:30:00.123456 UTC", time.Date(2026, 6, 1, 9, 30, 0, 123456000, time.UTC)},
		"rfc3339":             {"2026-06-01T09:30:00Z", time.Date(2026, 6, 1, 9, 30, 0, 0, time.UTC)},
		"epoch_plain":         {"1748995200", time.Date(2025, 6, 4, 0, 0, 0, 0, time.UTC)},
		"epoch_scientific":    {"1.7489952e+09", time.Date(2025, 6, 4, 0, 0, 0, 0, time.UTC)},
	}
	for name, tc := range cases {
		t.Run(name, func(t *testing.T) {
			got, err := Parse(tc.in)
			if err != nil {
				t.Fatalf("Parse(%q) error = %v", tc.in, err)
			}
			if !got.Equal(tc.want) {
				t.Errorf("Parse(%q) = %v, want %v", tc.in, got, tc.want)
			}
			if got.Location() != time.UTC {
				t.Errorf("Parse(%q) location = %v, want UTC", tc.in, got.Location())
			}
		})
	}
}

func TestParseRejectsGarbage(t *testing.T) {
	if _, err := Parse("not-a-time"); err == nil {
		t.Error("Parse(not-a-time) succeeded, want error")
	}
}
