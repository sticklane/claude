package merge

import (
	"testing"
	"time"

	"github.com/sticklane/agentprof/internal/schema"
)

func sample(session string, t time.Time, marker int64) schema.Sample {
	return schema.Sample{
		Time:   t,
		Stack:  []string{"proj", "leaf"},
		Values: map[string]int64{"cost_microusd": marker},
		Labels: map[string]string{"source": "claude-code", "session": session},
	}
}

func sessionCounts(samples []schema.Sample) map[string]int {
	m := map[string]int{}
	for _, s := range samples {
		m[s.Labels["session"]]++
	}
	return m
}

func TestMergeDropsOverlappingSessionAndAppendsNewOnly(t *testing.T) {
	now := time.Now()
	recent := now.Add(-time.Hour)
	existing := []schema.Sample{
		sample("A", recent, 100), // will be superseded by fresh A
		sample("B", recent, 200), // no fresh B -> survives
	}
	fresh := []schema.Sample{
		sample("A", recent, 999), // authoritative reparse of A
		sample("C", recent, 300), // brand new session
	}

	got := Merge(existing, fresh, now)

	counts := sessionCounts(got)
	if counts["A"] != 1 {
		t.Errorf("session A count = %d, want 1 (stale existing dropped, not duplicated)", counts["A"])
	}
	if counts["B"] != 1 {
		t.Errorf("session B count = %d, want 1 (non-overlapping existing survives)", counts["B"])
	}
	if counts["C"] != 1 {
		t.Errorf("session C count = %d, want 1 (new-only fresh appended)", counts["C"])
	}
	// The surviving A must be the FRESH one, not the stale existing one.
	for _, s := range got {
		if s.Labels["session"] == "A" && s.Values["cost_microusd"] != 999 {
			t.Errorf("session A survivor marker = %d, want 999 (fresh, not stale)", s.Values["cost_microusd"])
		}
	}
}

func TestMergeEmptyFreshLeavesNonEvictedUntouched(t *testing.T) {
	now := time.Now()
	recent := now.Add(-2 * time.Hour)
	existing := []schema.Sample{
		sample("A", recent, 100),
		sample("B", recent, 200),
	}

	got := Merge(existing, nil, now)

	if len(got) != 2 {
		t.Fatalf("len(got) = %d, want 2 (empty fresh must leave non-evicted samples untouched)", len(got))
	}
	counts := sessionCounts(got)
	if counts["A"] != 1 || counts["B"] != 1 {
		t.Errorf("session counts = %v, want A=1 B=1", counts)
	}
}

func TestMergeEvictsSamplesOlderThanSevenDays(t *testing.T) {
	now := time.Now()
	old := now.Add(-8 * 24 * time.Hour) // outside the 7d window
	fresh1 := now.Add(-time.Hour)       // inside the window
	existing := []schema.Sample{
		sample("A", old, 100),    // evicted
		sample("B", fresh1, 200), // kept
	}

	got := Merge(existing, nil, now)

	counts := sessionCounts(got)
	if counts["A"] != 0 {
		t.Errorf("session A count = %d, want 0 (older than 7d must be evicted)", counts["A"])
	}
	if counts["B"] != 1 {
		t.Errorf("session B count = %d, want 1 (within 7d retained)", counts["B"])
	}
}

func TestMergeAllEvictedAndEmptyFreshYieldsEmpty(t *testing.T) {
	now := time.Now()
	old := now.Add(-10 * 24 * time.Hour)
	existing := []schema.Sample{
		sample("A", old, 100),
		sample("B", old, 200),
	}

	got := Merge(existing, nil, now)

	if len(got) != 0 {
		t.Errorf("len(got) = %d, want 0 (fully idle 7d window evicts everything)", len(got))
	}
}
