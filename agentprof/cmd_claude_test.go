package main

import (
	"bytes"
	"os"
	"path/filepath"
	"strings"
	"testing"
	"time"

	"github.com/sticklane/agentprof/internal/schema"
)

func TestClaudeCommandWritesProfileAndReportsSkippedLines(t *testing.T) {
	out := filepath.Join(t.TempDir(), "cc.pb.gz")
	var stdout, stderr bytes.Buffer

	code := run([]string{"claude", "--claude-dir", "testdata/claude-dir", "-o", out}, &stdout, &stderr)

	if code != 0 {
		t.Fatalf("exit code = %d, want 0; stderr: %s", code, stderr.String())
	}
	if _, err := os.Stat(out); err != nil {
		t.Errorf("profile not written: %v", err)
	}
	if !strings.Contains(stderr.String(), "skipped 1 unparseable lines") {
		t.Errorf("stderr = %q, want it to report the truncated fixture line", stderr.String())
	}
}

func TestClaudeCommandEmitsCanonicalJSONLOnStdout(t *testing.T) {
	var stdout, stderr bytes.Buffer

	code := run([]string{"claude", "--claude-dir", "testdata/claude-dir"}, &stdout, &stderr)

	if code != 0 {
		t.Fatalf("exit code = %d, want 0; stderr: %s", code, stderr.String())
	}
	samples, skipped, err := schema.Read(&stdout)
	if err != nil {
		t.Fatalf("stdout is not canonical JSONL: %v", err)
	}
	if skipped != 0 {
		t.Errorf("stdout contained %d invalid canonical lines, want 0", skipped)
	}
	if len(samples) != 10 {
		t.Errorf("got %d samples on stdout, want 10", len(samples))
	}
}

func TestClaudeCommandZeroSamplesExitsOneWithoutWritingFile(t *testing.T) {
	emptyDir := t.TempDir()
	out := filepath.Join(t.TempDir(), "cc.pb.gz")
	var stdout, stderr bytes.Buffer

	code := run([]string{"claude", "--claude-dir", emptyDir, "-o", out}, &stdout, &stderr)

	if code != 1 {
		t.Fatalf("exit code = %d, want 1", code)
	}
	if _, err := os.Stat(out); !os.IsNotExist(err) {
		t.Errorf("no file must be written with zero samples, stat err = %v", err)
	}
	if stderr.Len() == 0 {
		t.Error("want an error message on stderr")
	}
}

func TestClaudeCommandDaysFlagExcludesOldSessions(t *testing.T) {
	// Copy the fixture and age every file beyond the window.
	dir := t.TempDir()
	old := time.Now().Add(-90 * 24 * time.Hour)
	err := filepath.Walk("testdata/claude-dir", func(path string, info os.FileInfo, err error) error {
		if err != nil {
			return err
		}
		rel, err := filepath.Rel("testdata/claude-dir", path)
		if err != nil {
			return err
		}
		target := filepath.Join(dir, rel)
		if info.IsDir() {
			return os.MkdirAll(target, 0o755)
		}
		data, err := os.ReadFile(path)
		if err != nil {
			return err
		}
		if err := os.WriteFile(target, data, 0o644); err != nil {
			return err
		}
		return os.Chtimes(target, old, old)
	})
	if err != nil {
		t.Fatal(err)
	}
	var stdout, stderr bytes.Buffer

	code := run([]string{"claude", "--claude-dir", dir, "--days", "30"}, &stdout, &stderr)

	if code != 1 {
		t.Errorf("exit code = %d, want 1 (all sessions out of window means zero samples)", code)
	}
	if stdout.Len() != 0 {
		t.Errorf("stdout = %q, want empty", stdout.String())
	}
}
