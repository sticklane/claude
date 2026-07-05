package pprofenc

import (
	"bytes"
	"testing"
	"time"

	"github.com/sticklane/agentprof/internal/schema"
)

func mustTime(t *testing.T, s string) time.Time {
	t.Helper()
	ts, err := time.Parse(time.RFC3339, s)
	if err != nil {
		t.Fatalf("parse time %q: %v", s, err)
	}
	return ts
}

func testSamples(t *testing.T) []schema.Sample {
	t.Helper()
	return []schema.Sample{
		{
			Time:   mustTime(t, "2026-07-01T09:15:00Z"),
			Stack:  []string{"proj", "skill", "model-a"},
			Values: map[string]int64{"input_tokens": 100, "cost_microusd": 42, "calls": 1},
			Labels: map[string]string{"source": "test", "region": "us"},
		},
		{
			Time:   mustTime(t, "2026-07-01T09:17:30Z"),
			Stack:  []string{"proj", "skill", "model-a"},
			Values: map[string]int64{"wall_ms": 250, "calls": 1},
		},
	}
}

func TestBuildSampleTypesAreUnionSortedWithCostFirst(t *testing.T) {
	prof, err := Build(testSamples(t))
	if err != nil {
		t.Fatalf("Build: %v", err)
	}
	want := []struct{ typ, unit string }{
		{"cost_microusd", "microusd"},
		{"calls", "count"},
		{"input_tokens", "tokens"},
		{"wall_ms", "milliseconds"},
	}
	if len(prof.SampleType) != len(want) {
		t.Fatalf("got %d sample types, want %d", len(prof.SampleType), len(want))
	}
	for i, w := range want {
		if prof.SampleType[i].Type != w.typ || prof.SampleType[i].Unit != w.unit {
			t.Errorf("SampleType[%d] = %s/%s, want %s/%s",
				i, prof.SampleType[i].Type, prof.SampleType[i].Unit, w.typ, w.unit)
		}
	}
	if prof.DefaultSampleType != "cost_microusd" {
		t.Errorf("DefaultSampleType = %q, want cost_microusd", prof.DefaultSampleType)
	}
}

func TestBuildDefaultSampleTypeIsFirstSortedWhenNoCost(t *testing.T) {
	samples := []schema.Sample{{
		Time:   mustTime(t, "2026-07-01T09:15:00Z"),
		Stack:  []string{"a"},
		Values: map[string]int64{"wall_ms": 5, "calls": 2},
	}}
	prof, err := Build(samples)
	if err != nil {
		t.Fatalf("Build: %v", err)
	}
	if prof.DefaultSampleType != "calls" {
		t.Errorf("DefaultSampleType = %q, want calls", prof.DefaultSampleType)
	}
}

func TestBuildMissingMetricContributesZero(t *testing.T) {
	prof, err := Build(testSamples(t))
	if err != nil {
		t.Fatalf("Build: %v", err)
	}
	// Sample types: cost_microusd, calls, input_tokens, wall_ms.
	// Second sample has only wall_ms and calls.
	got := prof.Sample[1].Value
	want := []int64{0, 1, 0, 250}
	if len(got) != len(want) {
		t.Fatalf("sample value len = %d, want %d", len(got), len(want))
	}
	for i := range want {
		if got[i] != want[i] {
			t.Errorf("Sample[1].Value[%d] = %d, want %d", i, got[i], want[i])
		}
	}
}

func TestBuildStackIsLeafFirstInLocations(t *testing.T) {
	prof, err := Build(testSamples(t))
	if err != nil {
		t.Fatalf("Build: %v", err)
	}
	locs := prof.Sample[0].Location
	if len(locs) != 3 {
		t.Fatalf("got %d locations, want 3", len(locs))
	}
	// Schema stack is root-first ["proj","skill","model-a"]; pprof Location
	// lists are leaf-first, so the first location must be model-a.
	wantOrder := []string{"model-a", "skill", "proj"}
	for i, w := range wantOrder {
		if got := locs[i].Line[0].Function.Name; got != w {
			t.Errorf("Location[%d] function = %q, want %q", i, got, w)
		}
	}
}

func TestBuildDedupsFunctionsAndLocationsByFrameName(t *testing.T) {
	prof, err := Build(testSamples(t))
	if err != nil {
		t.Fatalf("Build: %v", err)
	}
	// Two samples share the identical 3-frame stack.
	if len(prof.Function) != 3 {
		t.Errorf("got %d functions, want 3 (deduped)", len(prof.Function))
	}
	if len(prof.Location) != 3 {
		t.Errorf("got %d locations, want 3 (deduped)", len(prof.Location))
	}
	if prof.Sample[0].Location[0] != prof.Sample[1].Location[0] {
		t.Error("identical frames should reuse the same *Location")
	}
}

func TestBuildLabelsBecomeStringLabels(t *testing.T) {
	prof, err := Build(testSamples(t))
	if err != nil {
		t.Fatalf("Build: %v", err)
	}
	lab := prof.Sample[0].Label
	if got := lab["source"]; len(got) != 1 || got[0] != "test" {
		t.Errorf(`Label["source"] = %v, want ["test"]`, got)
	}
	if got := lab["region"]; len(got) != 1 || got[0] != "us" {
		t.Errorf(`Label["region"] = %v, want ["us"]`, got)
	}
	if prof.Sample[1].Label != nil && len(prof.Sample[1].Label) != 0 {
		t.Errorf("unlabeled sample got labels %v", prof.Sample[1].Label)
	}
}

func TestBuildTimeAndDurationDerivedFromData(t *testing.T) {
	samples := testSamples(t)
	prof, err := Build(samples)
	if err != nil {
		t.Fatalf("Build: %v", err)
	}
	min := samples[0].Time
	max := samples[1].Time
	if prof.TimeNanos != min.UnixNano() {
		t.Errorf("TimeNanos = %d, want %d (min sample time)", prof.TimeNanos, min.UnixNano())
	}
	if want := max.Sub(min).Nanoseconds(); prof.DurationNanos != want {
		t.Errorf("DurationNanos = %d, want %d (max-min)", prof.DurationNanos, want)
	}
}

func TestBuildProfileIsValid(t *testing.T) {
	prof, err := Build(testSamples(t))
	if err != nil {
		t.Fatalf("Build: %v", err)
	}
	if err := prof.CheckValid(); err != nil {
		t.Errorf("CheckValid: %v", err)
	}
}

func TestBuildIsByteDeterministicIncludingGzip(t *testing.T) {
	var bufs [2]bytes.Buffer
	for i := range bufs {
		prof, err := Build(testSamples(t))
		if err != nil {
			t.Fatalf("Build: %v", err)
		}
		if err := prof.Write(&bufs[i]); err != nil {
			t.Fatalf("Write: %v", err)
		}
	}
	if !bytes.Equal(bufs[0].Bytes(), bufs[1].Bytes()) {
		t.Error("two encodings of identical input differ byte-for-byte")
	}
}

func TestBuildReturnsErrorOnZeroSamples(t *testing.T) {
	if _, err := Build(nil); err == nil {
		t.Error("Build(nil) should return an error")
	}
}

func TestBuildUnknownMetricGetsCountUnit(t *testing.T) {
	samples := []schema.Sample{{
		Time:   mustTime(t, "2026-07-01T09:15:00Z"),
		Stack:  []string{"a"},
		Values: map[string]int64{"weirdness": 7},
	}}
	prof, err := Build(samples)
	if err != nil {
		t.Fatalf("Build: %v", err)
	}
	if prof.SampleType[0].Type != "weirdness" || prof.SampleType[0].Unit != "count" {
		t.Errorf("got %s/%s, want weirdness/count",
			prof.SampleType[0].Type, prof.SampleType[0].Unit)
	}
}
