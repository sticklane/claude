// Package pprofenc encodes canonical agentprof samples as pprof profiles
// (SPEC R2, R3). Output is deterministic: identical input yields
// byte-identical profiles.
package pprofenc

import (
	"errors"
	"sort"
	"strings"

	"github.com/google/pprof/profile"

	"github.com/sticklane/agentprof/internal/schema"
)

// unitFor maps a metric name to its pprof unit per the SCHEMA.md table.
func unitFor(metric string) string {
	switch {
	case metric == "cost_microusd":
		return "microusd"
	case metric == "wall_ms", metric == "duration_ms":
		return "milliseconds"
	case strings.HasSuffix(metric, "_tokens"):
		return "tokens"
	default:
		return "count"
	}
}

// metricOrder returns the union of metric keys across samples, sorted, with
// cost_microusd first when present.
func metricOrder(samples []schema.Sample) []string {
	seen := make(map[string]bool)
	var metrics []string
	for _, s := range samples {
		for k := range s.Values {
			if !seen[k] {
				seen[k] = true
				metrics = append(metrics, k)
			}
		}
	}
	sort.Slice(metrics, func(i, j int) bool {
		if metrics[i] == "cost_microusd" || metrics[j] == "cost_microusd" {
			return metrics[i] == "cost_microusd"
		}
		return metrics[i] < metrics[j]
	})
	return metrics
}

// Build converts canonical samples into a pprof profile. Sample types are the
// sorted union of metric keys (cost_microusd first and default when present);
// stacks are reversed to pprof's leaf-first order; labels become string
// labels; TimeNanos/DurationNanos come from the min/max sample time.
func Build(samples []schema.Sample) (*profile.Profile, error) {
	if len(samples) == 0 {
		return nil, errors.New("no samples")
	}
	metrics := metricOrder(samples)
	if len(metrics) == 0 {
		return nil, errors.New("no metrics in any sample")
	}

	p := &profile.Profile{DefaultSampleType: metrics[0]}
	for _, m := range metrics {
		p.SampleType = append(p.SampleType, &profile.ValueType{Type: m, Unit: unitFor(m)})
	}

	locByName := make(map[string]*profile.Location)
	locFor := func(name string) *profile.Location {
		if loc, ok := locByName[name]; ok {
			return loc
		}
		fn := &profile.Function{
			ID:         uint64(len(p.Function) + 1),
			Name:       name,
			SystemName: name,
		}
		p.Function = append(p.Function, fn)
		loc := &profile.Location{
			ID:   uint64(len(p.Location) + 1),
			Line: []profile.Line{{Function: fn}},
		}
		p.Location = append(p.Location, loc)
		locByName[name] = loc
		return loc
	}

	minTime, maxTime := samples[0].Time, samples[0].Time
	for _, s := range samples {
		if s.Time.Before(minTime) {
			minTime = s.Time
		}
		if s.Time.After(maxTime) {
			maxTime = s.Time
		}

		locs := make([]*profile.Location, 0, len(s.Stack))
		for i := len(s.Stack) - 1; i >= 0; i-- { // schema is root-first; pprof is leaf-first
			locs = append(locs, locFor(s.Stack[i]))
		}
		values := make([]int64, len(metrics))
		for i, m := range metrics {
			values[i] = s.Values[m]
		}
		var labels map[string][]string
		if len(s.Labels) > 0 {
			labels = make(map[string][]string, len(s.Labels))
			for k, v := range s.Labels {
				labels[k] = []string{v}
			}
		}
		p.Sample = append(p.Sample, &profile.Sample{
			Location: locs,
			Value:    values,
			Label:    labels,
		})
	}

	p.TimeNanos = minTime.UnixNano()
	p.DurationNanos = maxTime.Sub(minTime).Nanoseconds()
	return p, nil
}
