package schema

import (
	"encoding/json"
	"os"
	"path/filepath"
	"strings"
	"testing"
	"time"
)

const validLine = `{"time":"2026-07-02T18:04:11Z","stack":["fooszone","/build","agent:scout","claude-haiku-4-5"],"values":{"input_tokens":10101,"output_tokens":1560,"cost_microusd":41230,"calls":1},"labels":{"source":"claude-code","session":"7c576eff"}}`

func TestReadValidSampleDecodesAllFields(t *testing.T) {
	samples, skipped, err := Read(strings.NewReader(validLine + "\n"))
	if err != nil {
		t.Fatalf("Read returned error: %v", err)
	}
	if skipped != 0 {
		t.Errorf("skipped = %d, want 0", skipped)
	}
	if len(samples) != 1 {
		t.Fatalf("len(samples) = %d, want 1", len(samples))
	}
	s := samples[0]
	wantTime := time.Date(2026, 7, 2, 18, 4, 11, 0, time.UTC)
	if !s.Time.Equal(wantTime) {
		t.Errorf("Time = %v, want %v", s.Time, wantTime)
	}
	wantStack := []string{"fooszone", "/build", "agent:scout", "claude-haiku-4-5"}
	if len(s.Stack) != len(wantStack) {
		t.Fatalf("Stack = %v, want %v", s.Stack, wantStack)
	}
	for i := range wantStack {
		if s.Stack[i] != wantStack[i] {
			t.Errorf("Stack[%d] = %q, want %q", i, s.Stack[i], wantStack[i])
		}
	}
	if s.Values["input_tokens"] != 10101 || s.Values["output_tokens"] != 1560 ||
		s.Values["cost_microusd"] != 41230 || s.Values["calls"] != 1 {
		t.Errorf("Values = %v", s.Values)
	}
	if s.Labels["source"] != "claude-code" || s.Labels["session"] != "7c576eff" {
		t.Errorf("Labels = %v", s.Labels)
	}
}

func TestReadValidSampleWithoutLabelsOrUnknownMetric(t *testing.T) {
	// Unknown metric names and a missing labels map are valid per R2.
	line := `{"time":"2026-07-02T00:00:00Z","stack":["app"],"values":{"widgets_frobbed":7}}`
	samples, skipped, err := Read(strings.NewReader(line + "\n"))
	if err != nil {
		t.Fatalf("Read returned error: %v", err)
	}
	if skipped != 0 || len(samples) != 1 {
		t.Fatalf("samples=%d skipped=%d, want 1/0", len(samples), skipped)
	}
	if samples[0].Values["widgets_frobbed"] != 7 {
		t.Errorf("Values = %v, want widgets_frobbed=7", samples[0].Values)
	}
}

func TestReadValidationSkipRules(t *testing.T) {
	cases := []struct {
		name string
		line string
	}{
		{"bad JSON", `{"time":"2026-07-02T00:00:00Z","stack":["a"`},
		{"missing stack", `{"time":"2026-07-02T00:00:00Z","values":{"calls":1}}`},
		{"empty stack", `{"time":"2026-07-02T00:00:00Z","stack":[],"values":{"calls":1}}`},
		{"non-string in stack", `{"time":"2026-07-02T00:00:00Z","stack":["a",42],"values":{"calls":1}}`},
		{"negative value", `{"time":"2026-07-02T00:00:00Z","stack":["a"],"values":{"calls":-1}}`},
		{"non-integer value", `{"time":"2026-07-02T00:00:00Z","stack":["a"],"values":{"cost_microusd":1.5}}`},
		{"missing time", `{"stack":["a"],"values":{"calls":1}}`},
		{"non-RFC3339 time", `{"time":"2026-07-02 00:00:00","stack":["a"],"values":{"calls":1}}`},
		{"blank line", ``},
	}
	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			input := tc.line + "\n" + validLine + "\n"
			samples, skipped, err := Read(strings.NewReader(input))
			if err != nil {
				t.Fatalf("Read returned error: %v", err)
			}
			if skipped != 1 {
				t.Errorf("skipped = %d, want 1", skipped)
			}
			if len(samples) != 1 {
				t.Errorf("len(samples) = %d, want 1 (the valid line must survive)", len(samples))
			}
		})
	}
}

func TestReadValidationAcceptsLargeIntegerNotFloat(t *testing.T) {
	// json.Number decoding: 1560 passes, 1.5 is rejected (covered above).
	line := `{"time":"2026-07-02T00:00:00Z","stack":["a"],"values":{"output_tokens":1560}}`
	samples, skipped, err := Read(strings.NewReader(line + "\n"))
	if err != nil {
		t.Fatalf("Read returned error: %v", err)
	}
	if skipped != 0 || len(samples) != 1 {
		t.Fatalf("samples=%d skipped=%d, want 1/0", len(samples), skipped)
	}
	if samples[0].Values["output_tokens"] != 1560 {
		t.Errorf("output_tokens = %d, want 1560", samples[0].Values["output_tokens"])
	}
}

func TestMarshalLineRoundTripsThroughRead(t *testing.T) {
	s := Sample{
		Time:   time.Date(2026, 7, 2, 18, 4, 11, 0, time.UTC),
		Stack:  []string{"vertex-online-inference", "predict", "gemini-2.0-flash"},
		Values: map[string]int64{"wall_ms": 340, "calls": 1},
		Labels: map[string]string{"source": "vertex-online-inference"},
	}
	line, err := MarshalLine(s)
	if err != nil {
		t.Fatalf("MarshalLine returned error: %v", err)
	}
	if strings.ContainsRune(strings.TrimRight(string(line), "\n"), '\n') {
		t.Fatalf("MarshalLine output contains interior newline: %q", line)
	}
	var raw map[string]json.RawMessage
	if err := json.Unmarshal(line, &raw); err != nil {
		t.Fatalf("MarshalLine output is not valid JSON: %v", err)
	}
	got, skipped, err := Read(strings.NewReader(string(line) + "\n"))
	if err != nil {
		t.Fatalf("Read returned error: %v", err)
	}
	if skipped != 0 || len(got) != 1 {
		t.Fatalf("round-trip: samples=%d skipped=%d, want 1/0", len(got), skipped)
	}
	if !got[0].Time.Equal(s.Time) {
		t.Errorf("Time = %v, want %v", got[0].Time, s.Time)
	}
	if got[0].Values["wall_ms"] != 340 || got[0].Values["calls"] != 1 {
		t.Errorf("Values = %v", got[0].Values)
	}
	if got[0].Labels["source"] != "vertex-online-inference" {
		t.Errorf("Labels = %v", got[0].Labels)
	}
}

func TestMarshalLineValidPreservesSubsecondTime(t *testing.T) {
	s := Sample{
		Time:  time.Date(2026, 7, 2, 18, 4, 11, 250_000_000, time.UTC),
		Stack: []string{"app"},
	}
	line, err := MarshalLine(s)
	if err != nil {
		t.Fatalf("MarshalLine returned error: %v", err)
	}
	got, skipped, err := Read(strings.NewReader(string(line) + "\n"))
	if err != nil || skipped != 0 || len(got) != 1 {
		t.Fatalf("round-trip failed: samples=%d skipped=%d err=%v", len(got), skipped, err)
	}
	if !got[0].Time.Equal(s.Time) {
		t.Errorf("Time = %v, want %v (sub-second precision dropped)", got[0].Time, s.Time)
	}
}

func TestFixtureCustomSamplesValidCountAndSkipped(t *testing.T) {
	f, err := os.Open(filepath.Join("..", "..", "testdata", "samples-custom.jsonl"))
	if err != nil {
		t.Fatalf("open fixture: %v", err)
	}
	defer f.Close()
	samples, skipped, err := Read(f)
	if err != nil {
		t.Fatalf("Read returned error: %v", err)
	}
	if skipped != 2 {
		t.Errorf("skipped = %d, want exactly 2 (spec build acceptance)", skipped)
	}
	if len(samples) < 3 {
		t.Errorf("len(samples) = %d, want >= 3", len(samples))
	}
	hasCost := false
	for _, s := range samples {
		if s.Stack[0] != "vertex-online-inference" {
			t.Errorf("Stack root = %q, want vertex-online-inference", s.Stack[0])
		}
		if _, ok := s.Values["cost_microusd"]; ok {
			hasCost = true
		}
	}
	if !hasCost {
		t.Error("no valid sample carries cost_microusd (task 02 acceptance needs it)")
	}
}
