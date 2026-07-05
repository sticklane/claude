package main

import (
	"bytes"
	"os"
	"path/filepath"
	"strings"
	"testing"

	"github.com/google/pprof/profile"

	"github.com/sticklane/agentprof/internal/schema"
)

func TestBuildWritesProfileAndReportsSkippedLines(t *testing.T) {
	out := filepath.Join(t.TempDir(), "c.pb.gz")
	var stdout, stderr bytes.Buffer
	code := run([]string{"build", "testdata/samples-custom.jsonl", "-o", out}, &stdout, &stderr)
	if code != 0 {
		t.Fatalf("exit code = %d, want 0 (stderr: %s)", code, stderr.String())
	}
	if !strings.Contains(stderr.String(), "skipped 2 invalid lines") {
		t.Errorf("stderr = %q, want it to contain %q", stderr.String(), "skipped 2 invalid lines")
	}
	f, err := os.Open(out)
	if err != nil {
		t.Fatalf("open output: %v", err)
	}
	defer f.Close()
	prof, err := profile.Parse(f)
	if err != nil {
		t.Fatalf("output is not a parseable pprof profile: %v", err)
	}
	if len(prof.Sample) != 4 {
		t.Errorf("got %d samples, want 4 (6 lines - 2 invalid)", len(prof.Sample))
	}
}

func TestBuildNoSkippedLinesPrintsNoSkipMessage(t *testing.T) {
	dir := t.TempDir()
	in := filepath.Join(dir, "ok.jsonl")
	line := `{"time":"2026-07-01T09:15:00Z","stack":["a"],"values":{"calls":1}}` + "\n"
	if err := os.WriteFile(in, []byte(line), 0o644); err != nil {
		t.Fatalf("write input: %v", err)
	}
	var stdout, stderr bytes.Buffer
	code := run([]string{"build", in, "-o", filepath.Join(dir, "ok.pb.gz")}, &stdout, &stderr)
	if code != 0 {
		t.Fatalf("exit code = %d, want 0 (stderr: %s)", code, stderr.String())
	}
	if strings.Contains(stderr.String(), "skipped") {
		t.Errorf("stderr = %q, want no skip message when nothing was skipped", stderr.String())
	}
}

func TestBuildZeroValidSamplesExitsOneWithMessage(t *testing.T) {
	dir := t.TempDir()
	in := filepath.Join(dir, "bad.jsonl")
	if err := os.WriteFile(in, []byte("garbage\n"), 0o644); err != nil {
		t.Fatalf("write input: %v", err)
	}
	out := filepath.Join(dir, "x.pb.gz")
	var stdout, stderr bytes.Buffer
	code := run([]string{"build", in, "-o", out}, &stdout, &stderr)
	if code != 1 {
		t.Errorf("exit code = %d, want 1", code)
	}
	if stderr.Len() == 0 {
		t.Error("want an error message on stderr")
	}
	if _, err := os.Stat(out); !os.IsNotExist(err) {
		t.Errorf("no output file should be written (stat err = %v)", err)
	}
}

func TestBuildDefaultOutputIsStdoutJSONL(t *testing.T) {
	var stdout, stderr bytes.Buffer
	code := run([]string{"build", "testdata/samples-custom.jsonl"}, &stdout, &stderr)
	if code != 0 {
		t.Fatalf("exit code = %d, want 0 (stderr: %s)", code, stderr.String())
	}
	samples, skipped, err := schema.Read(&stdout)
	if err != nil {
		t.Fatalf("schema.Read on stdout: %v", err)
	}
	if skipped != 0 || len(samples) != 4 {
		t.Errorf("stdout JSONL: %d samples / %d skipped, want 4 / 0", len(samples), skipped)
	}
}

func TestBuildMultipleInputsAreMerged(t *testing.T) {
	dir := t.TempDir()
	in := filepath.Join(dir, "more.jsonl")
	line := `{"time":"2026-07-02T09:15:00Z","stack":["b"],"values":{"calls":1}}` + "\n"
	if err := os.WriteFile(in, []byte(line), 0o644); err != nil {
		t.Fatalf("write input: %v", err)
	}
	var stdout, stderr bytes.Buffer
	code := run([]string{"build", "testdata/samples-custom.jsonl", in}, &stdout, &stderr)
	if code != 0 {
		t.Fatalf("exit code = %d, want 0 (stderr: %s)", code, stderr.String())
	}
	samples, _, err := schema.Read(&stdout)
	if err != nil {
		t.Fatalf("schema.Read on stdout: %v", err)
	}
	if len(samples) != 5 {
		t.Errorf("got %d merged samples, want 5 (4 + 1)", len(samples))
	}
}

func TestBuildMissingInputFileExitsOne(t *testing.T) {
	var stdout, stderr bytes.Buffer
	code := run([]string{"build", "does-not-exist.jsonl"}, &stdout, &stderr)
	if code != 1 {
		t.Errorf("exit code = %d, want 1", code)
	}
}

func TestBuildNoInputFilesExitsTwo(t *testing.T) {
	var stdout, stderr bytes.Buffer
	code := run([]string{"build"}, &stdout, &stderr)
	if code != 2 {
		t.Errorf("exit code = %d, want 2", code)
	}
}
