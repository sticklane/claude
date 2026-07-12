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
	if len(samples) != 13 {
		t.Errorf("got %d samples on stdout, want 13 (10 model-call + 3 tool: samples)", len(samples))
	}
}

func TestClaudeReportsUnmatchedToolCallsOnStderr(t *testing.T) {
	var stdout, stderr bytes.Buffer

	code := run([]string{"claude", "--claude-dir", "testdata/claude-dir"}, &stdout, &stderr)

	if code != 0 {
		t.Fatalf("exit code = %d, want 0; stderr: %s", code, stderr.String())
	}
	// The fixture holds tool_use blocks with no matching tool_result; a real run
	// must surface those unmatched calls as a parse-stat on stderr.
	if !strings.Contains(stderr.String(), "unmatched tool call") {
		t.Errorf("stderr = %q, want it to report the unmatched (pending) tool calls", stderr.String())
	}
}

func TestClaudeKeepPendingEmitsPerCallPendingSamples(t *testing.T) {
	var stdout, stderr bytes.Buffer

	code := run([]string{"claude", "--claude-dir", "testdata/claude-dir", "--keep-pending"}, &stdout, &stderr)

	if code != 0 {
		t.Fatalf("exit code = %d, want 0; stderr: %s", code, stderr.String())
	}
	out := stdout.String()
	// --keep-pending restores per-call emission: unmatched calls keep their own
	// tool:(pending) sample with no consolidated pending_calls value.
	if !strings.Contains(out, "tool:(pending)") {
		t.Errorf("stdout = %q, want at least one tool:(pending) sample", out)
	}
	if strings.Contains(out, "pending_calls") {
		t.Errorf("stdout = %q, want no consolidated pending_calls value under --keep-pending", out)
	}
}

func TestClaudeMergeScrubsDenylistedFramesFromCachedSamples(t *testing.T) {
	dir := t.TempDir()
	// A rolling cache holding a frame written before the denylist existed.
	cached := schema.Sample{
		Time:   time.Now().Add(-time.Hour).UTC(),
		Stack:  []string{"myproject", "00", "skill:zz-test-private", "main", "claude-haiku-4-5"},
		Values: map[string]int64{"cost_micros": 1},
	}
	line, err := schema.MarshalLine(cached)
	if err != nil {
		t.Fatal(err)
	}
	cachePath := filepath.Join(dir, "cache.jsonl")
	if err := os.WriteFile(cachePath, append(line, '\n'), 0o600); err != nil {
		t.Fatal(err)
	}
	denylistPath := filepath.Join(dir, "frame-denylist")
	if err := os.WriteFile(denylistPath, []byte("zz-test\n"), 0o600); err != nil {
		t.Fatal(err)
	}

	var stdout, stderr bytes.Buffer
	// Empty --claude-dir → zero fresh samples; the merge re-emits the cache.
	code := run([]string{
		"claude", "--claude-dir", t.TempDir(),
		"--merge", cachePath,
		"--frame-denylist", denylistPath,
	}, &stdout, &stderr)

	if code != 0 {
		t.Fatalf("exit code = %d, want 0; stderr: %s", code, stderr.String())
	}
	if strings.Contains(stdout.String(), "zz-test") {
		t.Errorf("denied substring leaked from the rolling cache into merged output:\n%s", stdout.String())
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

func TestClaudeSinceWithExplicitDaysIsUsageError(t *testing.T) {
	out := filepath.Join(t.TempDir(), "cc.jsonl")
	var stdout, stderr bytes.Buffer

	code := run([]string{"claude", "--claude-dir", "testdata/claude-dir",
		"--since", "2020-01-01T00:00:00Z", "--days", "1", "-o", out}, &stdout, &stderr)

	if code == 0 {
		t.Fatalf("exit code = %d, want nonzero (--since + explicit --days is a usage error)", code)
	}
	msg := stderr.String()
	if !strings.Contains(msg, "since") || !strings.Contains(msg, "days") {
		t.Errorf("stderr = %q, want it to mention both --since and --days", msg)
	}
	if _, err := os.Stat(out); !os.IsNotExist(err) {
		t.Errorf("no output must be written on a usage error, stat err = %v", err)
	}
}

func TestClaudeSinceAloneWithDefaultDaysExitsZero(t *testing.T) {
	out := filepath.Join(t.TempDir(), "cc.jsonl")
	var stdout, stderr bytes.Buffer

	// --since alone leaves --days at its default 30; that must NOT be treated
	// as the mutually-exclusive case.
	code := run([]string{"claude", "--claude-dir", "testdata/claude-dir",
		"--since", "2020-01-01T00:00:00Z", "-o", out}, &stdout, &stderr)

	if code != 0 {
		t.Fatalf("exit code = %d, want 0; stderr: %s", code, stderr.String())
	}
	if _, err := os.Stat(out); err != nil {
		t.Errorf("output not written: %v", err)
	}
}

func TestClaudeMergeWithPbGzOutputIsUsageError(t *testing.T) {
	cache := filepath.Join(t.TempDir(), "cache.jsonl")
	writeCache(t, cache, []schema.Sample{mergeSample("A", time.Now().Add(-time.Hour))})
	out := filepath.Join(t.TempDir(), "cc.pb.gz")
	var stdout, stderr bytes.Buffer

	code := run([]string{"claude", "--claude-dir", "testdata/claude-dir",
		"--merge", cache, "-o", out}, &stdout, &stderr)

	if code == 0 {
		t.Fatalf("exit code = %d, want nonzero (--merge with .pb.gz -o is a usage error)", code)
	}
	if stderr.Len() == 0 {
		t.Error("want an error message on stderr")
	}
	if _, err := os.Stat(out); !os.IsNotExist(err) {
		t.Errorf("no output must be written on a usage error, stat err = %v", err)
	}
}

func TestClaudeMergeEmptyFreshKeepsNonEvictedAndExitsZero(t *testing.T) {
	// An empty claude-dir yields an empty fresh Collect() pass; the merge must
	// still exit 0 (bypassing the "no samples found" guard) and leave the
	// existing non-evicted cache samples in the output.
	emptyDir := t.TempDir()
	cache := filepath.Join(t.TempDir(), "cache.jsonl")
	writeCache(t, cache, []schema.Sample{
		mergeSample("A", time.Now().Add(-time.Hour)),
		mergeSample("B", time.Now().Add(-2*time.Hour)),
	})
	out := filepath.Join(t.TempDir(), "out.jsonl")
	var stdout, stderr bytes.Buffer

	code := run([]string{"claude", "--claude-dir", emptyDir,
		"--merge", cache, "-o", out}, &stdout, &stderr)

	if code != 0 {
		t.Fatalf("exit code = %d, want 0 (empty-fresh merge must not exit 1); stderr: %s", code, stderr.String())
	}
	f, err := os.Open(out)
	if err != nil {
		t.Fatalf("output not written: %v", err)
	}
	defer f.Close()
	samples, _, err := schema.Read(f)
	if err != nil {
		t.Fatalf("output is not valid JSONL: %v", err)
	}
	if len(samples) != 2 {
		t.Errorf("got %d merged samples, want 2 (both non-evicted cache samples retained)", len(samples))
	}
}

func TestClaudeMergeAllEvictedWritesEmptyJSONLAndExitsZero(t *testing.T) {
	// Every cache sample is older than 7d and fresh is empty: the merged result
	// is empty, which must write a valid empty JSONL file (never route through
	// output.Write's zero-sample error) and exit 0.
	emptyDir := t.TempDir()
	cache := filepath.Join(t.TempDir(), "cache.jsonl")
	old := time.Now().Add(-10 * 24 * time.Hour)
	writeCache(t, cache, []schema.Sample{mergeSample("A", old), mergeSample("B", old)})
	out := filepath.Join(t.TempDir(), "out.jsonl")
	var stdout, stderr bytes.Buffer

	code := run([]string{"claude", "--claude-dir", emptyDir,
		"--merge", cache, "-o", out}, &stdout, &stderr)

	if code != 0 {
		t.Fatalf("exit code = %d, want 0; stderr: %s", code, stderr.String())
	}
	info, err := os.Stat(out)
	if err != nil {
		t.Fatalf("empty JSONL file not written: %v", err)
	}
	if info.Size() != 0 {
		t.Errorf("output size = %d bytes, want 0 (empty merged result → empty file)", info.Size())
	}
}

func mergeSample(session string, ts time.Time) schema.Sample {
	return schema.Sample{
		Time:   ts,
		Stack:  []string{"proj", "leaf"},
		Values: map[string]int64{"cost_microusd": 100},
		Labels: map[string]string{"source": "claude-code", "session": session},
	}
}

func writeCache(t *testing.T, path string, samples []schema.Sample) {
	t.Helper()
	var buf bytes.Buffer
	for _, s := range samples {
		line, err := schema.MarshalLine(s)
		if err != nil {
			t.Fatal(err)
		}
		buf.Write(line)
		buf.WriteByte('\n')
	}
	if err := os.WriteFile(path, buf.Bytes(), 0o644); err != nil {
		t.Fatal(err)
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
