// Package merge maintains the rolling JSONL cache for `agentprof claude
// --merge`: it folds a fresh Collect() pass into an existing cache and evicts
// samples older than the 7-day window (workboard-weekly-cost-view R2).
package merge

import (
	"time"

	"github.com/sticklane/agentprof/internal/schema"
)

// Window is the rolling retention: samples whose Time is older than now-Window
// are evicted on every merge.
const Window = 7 * 24 * time.Hour

// Merge folds fresh samples into an existing cache: every existing sample whose
// session label appears among the fresh samples is dropped (the fresh reparse
// is authoritative for any session whose mtime advanced), the fresh samples are
// appended, then every remaining sample older than now-Window is evicted. Fresh
// may be empty (steady state) and the result may be empty (a fully idle window
// evicts everything); both are valid.
func Merge(existing, fresh []schema.Sample, now time.Time) []schema.Sample {
	freshSessions := make(map[string]bool, len(fresh))
	for _, s := range fresh {
		freshSessions[s.Labels["session"]] = true
	}

	merged := make([]schema.Sample, 0, len(existing)+len(fresh))
	for _, s := range existing {
		if freshSessions[s.Labels["session"]] {
			continue // superseded by the fresh reparse
		}
		merged = append(merged, s)
	}
	merged = append(merged, fresh...)

	cutoff := now.Add(-Window)
	kept := merged[:0]
	for _, s := range merged {
		if s.Time.Before(cutoff) {
			continue // outside the rolling window
		}
		kept = append(kept, s)
	}
	return kept
}
