package main

import (
	"bytes"
	"encoding/json"
	"os"
	"path/filepath"
	"slices"
	"strings"
	"testing"
)

func TestCmdVertexWritesJSONLToStdoutAndReportsSkips(t *testing.T) {
	var stdout, stderr bytes.Buffer
	code := run([]string{"vertex", "testdata/vertex-logs.json"}, &stdout, &stderr)
	if code != 0 {
		t.Fatalf("exit code = %d, want 0 (stderr: %s)", code, stderr.String())
	}
	if !strings.Contains(stderr.String(), "skipped 1") {
		t.Errorf("stderr = %q, want it to report 1 skipped row", stderr.String())
	}
	lines := strings.Split(strings.TrimSpace(stdout.String()), "\n")
	if len(lines) != 4 {
		t.Fatalf("stdout has %d lines, want 4", len(lines))
	}
	var sample struct {
		Time   string            `json:"time"`
		Stack  []string          `json:"stack"`
		Values map[string]int64  `json:"values"`
		Labels map[string]string `json:"labels"`
	}
	if err := json.Unmarshal([]byte(lines[0]), &sample); err != nil {
		t.Fatalf("first line is not valid JSON: %v", err)
	}
	// Spot-check the Gemini unary fixture row (fixturegen inventory).
	wantStack := []string{"proj-vertex", "us-central1", "gemini-2.0-flash", "GenerateContent"}
	if !slices.Equal(sample.Stack, wantStack) {
		t.Fatalf("stack = %v, want %v", sample.Stack, wantStack)
	}
	for name, want := range map[string]int64{
		"input_tokens": 1000, "output_tokens": 150, "cache_read_tokens": 200, "calls": 1,
	} {
		if sample.Values[name] != want {
			t.Errorf("values[%s] = %d, want %d", name, sample.Values[name], want)
		}
	}
	if sample.Labels["source"] != "vertex" {
		t.Errorf("labels[source] = %q, want vertex", sample.Labels["source"])
	}
	if !strings.HasSuffix(sample.Time, "Z") {
		t.Errorf("time = %q, want RFC3339 UTC (Z suffix)", sample.Time)
	}
}

func TestCmdVertexWritesProfileWithDashO(t *testing.T) {
	out := filepath.Join(t.TempDir(), "v.pb.gz")
	var stdout, stderr bytes.Buffer
	code := run([]string{"vertex", "testdata/vertex-logs.json", "-o", out}, &stdout, &stderr)
	if code != 0 {
		t.Fatalf("exit code = %d, want 0 (stderr: %s)", code, stderr.String())
	}
	if !strings.Contains(stderr.String(), "skipped 1") {
		t.Errorf("stderr = %q, want it to report 1 skipped row", stderr.String())
	}
}

func TestCmdVertexWithoutInputFileExitsTwo(t *testing.T) {
	var stdout, stderr bytes.Buffer
	code := run([]string{"vertex"}, &stdout, &stderr)
	if code != 2 {
		t.Errorf("exit code = %d, want 2", code)
	}
	if !strings.Contains(stderr.String(), "usage") {
		t.Errorf("stderr = %q, want a usage message", stderr.String())
	}
}

func TestCmdVertexWithMissingFileExitsOne(t *testing.T) {
	var stdout, stderr bytes.Buffer
	code := run([]string{"vertex", "testdata/no-such-file.json"}, &stdout, &stderr)
	if code != 1 {
		t.Errorf("exit code = %d, want 1", code)
	}
}

func TestCmdVertexAllInvalidFileReportsNoValidRowsAndExitsOne(t *testing.T) {
	// An empty log export yields no samples, so the empty-check fires.
	path := filepath.Join(t.TempDir(), "empty.json")
	if err := os.WriteFile(path, []byte(`[]`), 0o644); err != nil {
		t.Fatalf("write fixture: %v", err)
	}
	var stdout, stderr bytes.Buffer
	code := run([]string{"vertex", path}, &stdout, &stderr)
	if code != 1 {
		t.Errorf("exit code = %d, want 1", code)
	}
	if !strings.Contains(stderr.String(), "agentprof vertex: no valid rows in input") {
		t.Errorf("stderr = %q, want it to report no valid rows in input", stderr.String())
	}
}
