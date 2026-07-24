package pricing

import (
	"strings"
	"testing"
	"time"
)

func fetchedTime(t *testing.T) time.Time {
	t.Helper()
	ft, err := time.Parse("2006-01-02", Fetched)
	if err != nil {
		t.Fatalf("Fetched %q is not a valid date: %v", Fetched, err)
	}
	return ft
}

func TestStalenessFreshWithinThreshold(t *testing.T) {
	now := fetchedTime(t).Add(30 * 24 * time.Hour)
	if _, stale := Staleness(now); stale {
		t.Error("30 days after Fetched should not be stale (threshold 90d)")
	}
	if w := StalenessWarning(now); w != "" {
		t.Errorf("expected no warning when fresh, got %q", w)
	}
}

func TestStalenessBeyondThresholdWarns(t *testing.T) {
	now := fetchedTime(t).Add(120 * 24 * time.Hour)
	age, stale := Staleness(now)
	if !stale {
		t.Fatal("120 days after Fetched should be stale (threshold 90d)")
	}
	if age <= StaleAfter {
		t.Errorf("age %v should exceed StaleAfter %v", age, StaleAfter)
	}
	w := StalenessWarning(now)
	if w == "" {
		t.Fatal("expected a warning when stale")
	}
	if !strings.Contains(w, Fetched) {
		t.Errorf("warning should cite the Fetched date %q: %q", Fetched, w)
	}
}
