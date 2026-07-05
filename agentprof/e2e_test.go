package main

import (
	"bytes"
	"os"
	"path/filepath"
	"strings"
	"testing"

	"github.com/google/pprof/profile"
)

// buildMixedProfile runs the full fixture pipeline (claude adapter + gcp
// adapter + build) and returns the parsed mixed-source profile (R10).
func buildMixedProfile(t *testing.T) *profile.Profile {
	t.Helper()
	dir := t.TempDir()
	claudeOut := filepath.Join(dir, "a.jsonl")
	gcpOut := filepath.Join(dir, "b.jsonl")
	mixedOut := filepath.Join(dir, "all.pb.gz")

	var stdout, stderr bytes.Buffer
	if code := run([]string{"claude", "--claude-dir", "testdata/claude-dir", "-o", claudeOut}, &stdout, &stderr); code != 0 {
		t.Fatalf("claude adapter exited %d: %s", code, stderr.String())
	}
	if code := run([]string{"gcp", "testdata/gcp-billing.json", "-o", gcpOut}, &stdout, &stderr); code != 0 {
		t.Fatalf("gcp adapter exited %d: %s", code, stderr.String())
	}
	if code := run([]string{"build", claudeOut, gcpOut, "-o", mixedOut}, &stdout, &stderr); code != 0 {
		t.Fatalf("build exited %d: %s", code, stderr.String())
	}

	f, err := os.Open(mixedOut)
	if err != nil {
		t.Fatalf("open mixed profile: %v", err)
	}
	defer f.Close()
	prof, err := profile.Parse(f)
	if err != nil {
		t.Fatalf("parse mixed profile: %v", err)
	}
	return prof
}

// sampleTypeIndex returns the index of the named sample type, or -1.
func sampleTypeIndex(prof *profile.Profile, name string) int {
	for i, st := range prof.SampleType {
		if st.Type == name {
			return i
		}
	}
	return -1
}

// samplesBySource partitions samples on the source label.
func samplesBySource(prof *profile.Profile, source string) []*profile.Sample {
	var out []*profile.Sample
	for _, s := range prof.Sample {
		for _, v := range s.Label["source"] {
			if v == source {
				out = append(out, s)
			}
		}
	}
	return out
}

func TestMixedProfileUsesCostAsDefaultSampleType(t *testing.T) {
	prof := buildMixedProfile(t)

	if prof.DefaultSampleType != "cost_microusd" {
		t.Errorf("default sample type = %q, want cost_microusd", prof.DefaultSampleType)
	}
	idx := sampleTypeIndex(prof, "cost_microusd")
	if idx == -1 {
		t.Fatal("cost_microusd sample type missing from mixed profile")
	}
	if unit := prof.SampleType[idx].Unit; unit != "microusd" {
		t.Errorf("cost_microusd unit = %q, want microusd", unit)
	}
}

func TestMixedProfileCostComparesBothSources(t *testing.T) {
	prof := buildMixedProfile(t)
	costIdx := sampleTypeIndex(prof, "cost_microusd")
	if costIdx == -1 {
		t.Fatal("cost_microusd sample type missing")
	}

	for _, source := range []string{"claude-code", "gcp"} {
		samples := samplesBySource(prof, source)
		if len(samples) == 0 {
			t.Fatalf("no samples with source=%s in mixed profile", source)
		}
		var total int64
		for _, s := range samples {
			total += s.Value[costIdx]
		}
		if total <= 0 {
			t.Errorf("source=%s total cost_microusd = %d, want > 0", source, total)
		}
	}
}

func TestMixedProfileTokenMetricsAreZeroForGCPSamples(t *testing.T) {
	prof := buildMixedProfile(t)

	tokenIdxs := map[string]int{}
	for _, name := range []string{"input_tokens", "output_tokens", "cache_read_tokens", "cache_write_tokens"} {
		idx := sampleTypeIndex(prof, name)
		if idx == -1 {
			t.Fatalf("token metric %s missing from mixed profile (R2 unioning)", name)
		}
		tokenIdxs[name] = idx
	}

	for _, s := range samplesBySource(prof, "gcp") {
		for name, idx := range tokenIdxs {
			if s.Value[idx] != 0 {
				t.Errorf("gcp sample has %s = %d, want 0", name, s.Value[idx])
			}
		}
	}

	// Claude samples must actually carry tokens, or the zero check above is vacuous.
	var claudeTokens int64
	for _, s := range samplesBySource(prof, "claude-code") {
		claudeTokens += s.Value[tokenIdxs["output_tokens"]]
	}
	if claudeTokens <= 0 {
		t.Errorf("claude-code samples total output_tokens = %d, want > 0", claudeTokens)
	}
}

// frameNames returns the sample's frame names (order as encoded).
func frameNames(s *profile.Sample) []string {
	var out []string
	for _, loc := range s.Location {
		for _, line := range loc.Line {
			out = append(out, line.Function.Name)
		}
	}
	return out
}

func TestMixedProfileContainsDepthTwoSubagentStack(t *testing.T) {
	prof := buildMixedProfile(t)

	// A depth-1 subagent stack is 6 frames; only a working spawn chain
	// produces 7+ frames with two agent: frames (R4/R9).
	for _, s := range samplesBySource(prof, "claude-code") {
		frames := frameNames(s)
		agents := 0
		for _, f := range frames {
			if strings.HasPrefix(f, "agent:") {
				agents++
			}
		}
		if agents >= 2 && len(frames) >= 7 {
			return
		}
	}
	t.Error("no claude-code sample has a depth-2 stack (>=7 frames with two agent: frames)")
}

func TestMixedProfileContainsUnlinkedSubagentStack(t *testing.T) {
	prof := buildMixedProfile(t)

	for _, s := range samplesBySource(prof, "claude-code") {
		for _, f := range frameNames(s) {
			if f == "(unlinked)" {
				return
			}
		}
	}
	t.Error("no claude-code sample carries the (unlinked) frame (R5)")
}

func TestMixedProfileTagfocusSourceGCPIsolatesGCPFrames(t *testing.T) {
	prof := buildMixedProfile(t)

	gcpSamples := samplesBySource(prof, "gcp")
	if len(gcpSamples) == 0 {
		t.Fatal("no samples with source=gcp in mixed profile")
	}

	frames := map[string]bool{}
	for _, s := range gcpSamples {
		for _, loc := range s.Location {
			for _, line := range loc.Line {
				frames[line.Function.Name] = true
			}
		}
	}

	// GCP stacks are [project.id, service.description, sku.description].
	for _, want := range []string{"proj-fooszone", "Vertex AI", "Vertex AI Online Prediction"} {
		if !frames[want] {
			t.Errorf("gcp samples missing expected frame %q; got %v", want, frames)
		}
	}
	// No Claude frames may leak into source=gcp samples.
	for frame := range frames {
		if strings.HasPrefix(frame, "claude-") || strings.HasPrefix(frame, "agent:") || frame == "main" || frame == "(no skill)" {
			t.Errorf("gcp sample contains Claude-shaped frame %q", frame)
		}
	}
}
