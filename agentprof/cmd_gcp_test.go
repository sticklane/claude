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

func TestCmdGCPWritesJSONLToStdoutAndReportsSkips(t *testing.T) {
	var stdout, stderr bytes.Buffer
	code := run([]string{"gcp", "testdata/gcp-billing.json"}, &stdout, &stderr)
	if code != 0 {
		t.Fatalf("exit code = %d, want 0 (stderr: %s)", code, stderr.String())
	}
	if !strings.Contains(stderr.String(), "skipped 2") {
		t.Errorf("stderr = %q, want it to report 2 skipped rows", stderr.String())
	}
	lines := strings.Split(strings.TrimSpace(stdout.String()), "\n")
	if len(lines) != 6 {
		t.Fatalf("stdout has %d lines, want 6", len(lines))
	}
	var sample struct {
		Time   string            `json:"time"`
		Stack  []string          `json:"stack"`
		Labels map[string]string `json:"labels"`
	}
	if err := json.Unmarshal([]byte(lines[0]), &sample); err != nil {
		t.Fatalf("first line is not valid JSON: %v", err)
	}
	if len(sample.Stack) != 3 {
		t.Errorf("stack = %v, want 3 frames", sample.Stack)
	}
	if sample.Labels["source"] != "gcp" {
		t.Errorf("labels[source] = %q, want gcp", sample.Labels["source"])
	}
	if !strings.HasSuffix(sample.Time, "Z") {
		t.Errorf("time = %q, want RFC3339 UTC (Z suffix)", sample.Time)
	}
}

func TestCmdGCPWritesProfileWithDashO(t *testing.T) {
	out := filepath.Join(t.TempDir(), "g.pb.gz")
	var stdout, stderr bytes.Buffer
	code := run([]string{"gcp", "testdata/gcp-billing.json", "-o", out}, &stdout, &stderr)
	if code != 0 {
		t.Fatalf("exit code = %d, want 0 (stderr: %s)", code, stderr.String())
	}
	if !strings.Contains(stderr.String(), "skipped 2") {
		t.Errorf("stderr = %q, want it to report 2 skipped rows", stderr.String())
	}
}

func TestCmdGCPWithoutInputFileExitsTwo(t *testing.T) {
	var stdout, stderr bytes.Buffer
	code := run([]string{"gcp"}, &stdout, &stderr)
	if code != 2 {
		t.Errorf("exit code = %d, want 2", code)
	}
}

func TestCmdGCPWithMissingFileExitsOne(t *testing.T) {
	var stdout, stderr bytes.Buffer
	code := run([]string{"gcp", "testdata/no-such-file.json"}, &stdout, &stderr)
	if code != 1 {
		t.Errorf("exit code = %d, want 1", code)
	}
}

func TestCmdGCPAllInvalidFileReportsNoValidRowsAndExitsOne(t *testing.T) {
	// Every row is missing required fields, so all are skipped and none survive.
	path := filepath.Join(t.TempDir(), "all-invalid.json")
	if err := os.WriteFile(path, []byte(`[{"project":{}},{"service":{"description":"x"}}]`), 0o644); err != nil {
		t.Fatalf("write fixture: %v", err)
	}
	var stdout, stderr bytes.Buffer
	code := run([]string{"gcp", path}, &stdout, &stderr)
	if code != 1 {
		t.Errorf("exit code = %d, want 1", code)
	}
	if !strings.Contains(stderr.String(), "agentprof gcp: no valid rows in input") {
		t.Errorf("stderr = %q, want it to report no valid rows in input", stderr.String())
	}
}

func TestCmdGCPFrameLabelsReachGCPParse(t *testing.T) {
	// --frame-labels team must reach gcp.Parse, which inserts a "team:vision"
	// frame after the project for the row carrying that billing label.
	var stdout, stderr bytes.Buffer
	code := run([]string{"gcp", "testdata/gcp-billing.json", "--frame-labels", "team"}, &stdout, &stderr)
	if code != 0 {
		t.Fatalf("exit code = %d, want 0 (stderr: %s)", code, stderr.String())
	}
	var found bool
	for _, line := range strings.Split(strings.TrimSpace(stdout.String()), "\n") {
		var sample struct {
			Stack []string `json:"stack"`
		}
		if err := json.Unmarshal([]byte(line), &sample); err != nil {
			t.Fatalf("line is not valid JSON: %v", err)
		}
		if slices.Contains(sample.Stack, "team:vision") {
			found = true
		}
	}
	if !found {
		t.Errorf("no sample stack contained the team:vision frame; --frame-labels did not reach gcp.Parse (stdout: %s)", stdout.String())
	}
}
