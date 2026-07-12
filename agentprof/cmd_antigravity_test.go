package main

import (
	"bytes"
	"encoding/json"
	"io"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

// stageAntigravityFixture copies the committed real fixture db into a fresh
// temp <dir>/conversations/ and returns <dir>. Reading a byte-copy rather than
// the tracked file keeps SQLite's read-only WAL sidecars (-wal/-shm, created
// because the fixture is a WAL-mode db) out of the tracked testdata/ directory.
func stageAntigravityFixture(t *testing.T) string {
	t.Helper()
	const src = "internal/antigravity/testdata/conversations/d147c9da-7c14-4e02-a386-156a72b7bf99.db"
	dir := t.TempDir()
	conv := filepath.Join(dir, "conversations")
	if err := os.MkdirAll(conv, 0o755); err != nil {
		t.Fatal(err)
	}
	in, err := os.Open(src)
	if err != nil {
		t.Fatal(err)
	}
	defer in.Close()
	out, err := os.Create(filepath.Join(conv, filepath.Base(src)))
	if err != nil {
		t.Fatal(err)
	}
	if _, err := io.Copy(out, in); err != nil {
		t.Fatal(err)
	}
	if err := out.Close(); err != nil {
		t.Fatal(err)
	}
	return dir
}

func TestCmdAntigravityZeroSamplesExitsOneWithNoSamplesFound(t *testing.T) {
	emptyDir := filepath.Join(t.TempDir(), "does-not-exist")
	var stdout, stderr bytes.Buffer

	code := run([]string{"antigravity", "--antigravity-dir", emptyDir, "--days", "3650"}, &stdout, &stderr)

	if code != 1 {
		t.Fatalf("exit code = %d, want 1; stderr: %s", code, stderr.String())
	}
	if !strings.Contains(stderr.String(), "no samples found") {
		t.Errorf("stderr = %q, want it to contain %q", stderr.String(), "no samples found")
	}
}

func TestCmdAntigravitySummaryEmitsSummaryRowJSON(t *testing.T) {
	dir := stageAntigravityFixture(t)
	var stdout, stderr bytes.Buffer

	code := run([]string{"antigravity", "-o", "summary", "--antigravity-dir", dir, "--days", "3650"}, &stdout, &stderr)

	if code != 0 {
		t.Fatalf("exit code = %d, want 0; stderr: %s", code, stderr.String())
	}
	var rows []summaryRow
	if err := json.Unmarshal(stdout.Bytes(), &rows); err != nil {
		t.Fatalf("stdout is not a JSON array of summaryRow: %v\nstdout: %s", err, stdout.String())
	}
	if len(rows) == 0 {
		t.Fatalf("want at least one summary row from the fixture, got 0")
	}
	// Assert the row carries the summaryRow shape: a real session/model pair.
	if rows[0].Session == "" {
		t.Errorf("summary row has empty session: %+v", rows[0])
	}
	if rows[0].Model == "" {
		t.Errorf("summary row has empty model: %+v", rows[0])
	}
}
