package pricing

import (
	"fmt"
	"time"
)

// Fetched is the date the rate table in table.go was last verified against the
// published Claude pricing page, in "2006-01-02" form. It is the single source
// of truth for table freshness — Staleness compares it against the current
// date so drift is surfaced at runtime, not only in a stale code comment.
//
// Refresh procedure: re-check
// https://docs.claude.com/en/docs/about-claude/pricing, update every entry in
// table.go's `table` and any modeling notes (e.g. the Sonnet introductory
// rate), then set Fetched to the date you verified.
const Fetched = "2026-07-02"

// StaleAfter is how long the table is trusted before Staleness reports it as
// due for a refresh.
const StaleAfter = 90 * 24 * time.Hour

// Staleness reports the table's age at now and whether it exceeds StaleAfter.
// An unparseable Fetched date is reported as stale with a zero age, so a typo
// can never silently suppress the warning.
func Staleness(now time.Time) (age time.Duration, stale bool) {
	fetched, err := time.Parse("2006-01-02", Fetched)
	if err != nil {
		return 0, true
	}
	age = now.Sub(fetched)
	return age, age > StaleAfter
}

// StalenessWarning returns a one-line warning when the table is older than
// StaleAfter at now, or "" when it is still fresh. Callers print a non-empty
// result to stderr alongside summary output.
func StalenessWarning(now time.Time) string {
	age, stale := Staleness(now)
	if !stale {
		return ""
	}
	days := int(age.Hours() / 24)
	threshold := int(StaleAfter.Hours() / 24)
	return fmt.Sprintf(
		"warning: pricing table last verified %s (%d days ago, threshold %d); rates may be stale — refresh per internal/pricing/staleness.go",
		Fetched, days, threshold,
	)
}
