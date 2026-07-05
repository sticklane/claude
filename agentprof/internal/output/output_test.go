package output

import (
	"bytes"
	"os"
	"path/filepath"
	"strings"
	"testing"
	"time"

	"github.com/google/pprof/profile"

	"github.com/sticklane/agentprof/internal/schema"
)

func testSamples(t *testing.T) []schema.Sample {
	t.Helper()
	ts, err := time.Parse(time.RFC3339, "2026-07-01T09:15:00Z")
	if err != nil {
		t.Fatalf("parse time: %v", err)
	}
	return []schema.Sample{
		{
			Time:   ts,
			Stack:  []string{"proj", "model-a"},
			Values: map[string]int64{"cost_microusd": 42, "calls": 1},
			Labels: map[string]string{"source": "test"},
		},
		{
			Time:   ts.Add(30 * time.Second),
			Stack:  []string{"proj", "model-b"},
			Values: map[string]int64{"calls": 1},
		},
	}
}

func TestWritePbGzPathWritesGzippedProfile(t *testing.T) {
	path := filepath.Join(t.TempDir(), "out.pb.gz")
	if err := Write(testSamples(t), path, nil); err != nil {
		t.Fatalf("Write: %v", err)
	}
	f, err := os.Open(path)
	if err != nil {
		t.Fatalf("open output: %v", err)
	}
	defer f.Close()
	prof, err := profile.Parse(f)
	if err != nil {
		t.Fatalf("output is not a parseable pprof profile: %v", err)
	}
	if err := prof.CheckValid(); err != nil {
		t.Errorf("CheckValid: %v", err)
	}
	if len(prof.Sample) != 2 {
		t.Errorf("got %d samples, want 2", len(prof.Sample))
	}
}

func TestWriteEmptyPathWritesJSONLToStdout(t *testing.T) {
	var buf bytes.Buffer
	if err := Write(testSamples(t), "", &buf); err != nil {
		t.Fatalf("Write: %v", err)
	}
	assertJSONL(t, buf.String())
}

func TestWriteDashPathWritesJSONLToStdout(t *testing.T) {
	var buf bytes.Buffer
	if err := Write(testSamples(t), "-", &buf); err != nil {
		t.Fatalf("Write: %v", err)
	}
	assertJSONL(t, buf.String())
}

func TestWriteOtherPathWritesJSONLFile(t *testing.T) {
	path := filepath.Join(t.TempDir(), "out.jsonl")
	if err := Write(testSamples(t), path, nil); err != nil {
		t.Fatalf("Write: %v", err)
	}
	data, err := os.ReadFile(path)
	if err != nil {
		t.Fatalf("read output: %v", err)
	}
	assertJSONL(t, string(data))
}

// assertJSONL checks the text round-trips through the schema reader as two
// valid samples.
func assertJSONL(t *testing.T, text string) {
	t.Helper()
	samples, skipped, err := schema.Read(strings.NewReader(text))
	if err != nil {
		t.Fatalf("schema.Read: %v", err)
	}
	if skipped != 0 {
		t.Errorf("JSONL output has %d invalid lines", skipped)
	}
	if len(samples) != 2 {
		t.Errorf("got %d samples, want 2", len(samples))
	}
}

func TestWriteZeroSamplesReturnsErrorAndWritesNoFile(t *testing.T) {
	path := filepath.Join(t.TempDir(), "out.pb.gz")
	if err := Write(nil, path, nil); err == nil {
		t.Error("Write with zero samples should return an error")
	}
	if _, err := os.Stat(path); !os.IsNotExist(err) {
		t.Errorf("zero-samples Write must not create a file (stat err = %v)", err)
	}
}

func TestWriteZeroSamplesToJSONLPathAlsoErrors(t *testing.T) {
	path := filepath.Join(t.TempDir(), "out.jsonl")
	if err := Write(nil, path, nil); err == nil {
		t.Error("Write with zero samples should return an error")
	}
	if _, err := os.Stat(path); !os.IsNotExist(err) {
		t.Errorf("zero-samples Write must not create a file (stat err = %v)", err)
	}
}
