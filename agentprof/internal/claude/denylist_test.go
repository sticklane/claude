package claude

import (
	"os"
	"path/filepath"
	"strings"
	"testing"
	"time"

	"github.com/sticklane/agentprof/internal/schema"
)

// emitJSONL marshals samples to the wire JSONL the way output.writeJSONL does,
// so assertions run against exactly what would be written to disk.
func emitJSONL(t *testing.T, samples []schema.Sample) string {
	t.Helper()
	var b strings.Builder
	for _, s := range samples {
		line, err := schema.MarshalLine(s)
		if err != nil {
			t.Fatalf("MarshalLine: %v", err)
		}
		b.Write(line)
		b.WriteByte('\n')
	}
	return b.String()
}

func sampleWithStack(stack ...string) schema.Sample {
	return schema.Sample{
		Time:   time.Unix(0, 0).UTC(),
		Stack:  stack,
		Values: map[string]int64{"cost_micros": 1},
	}
}

func TestScrubFramesRedactsSkillFrameAndDropsSubstring(t *testing.T) {
	samples := []schema.Sample{
		sampleWithStack("myproject", "00", "skill:zz-test-private", "main", "claude-haiku-4-5"),
	}
	// Denylist lists a substring of the skill name, not the whole frame.
	ScrubFrames(samples, []string{"zz-test"})

	if got := samples[0].Stack[2]; got != "(redacted)" {
		t.Errorf("skill frame = %q, want %q", got, "(redacted)")
	}
	out := emitJSONL(t, samples)
	if strings.Contains(out, "zz-test") {
		t.Errorf("denied substring %q leaked into emitted JSONL:\n%s", "zz-test", out)
	}
}

func TestScrubFramesRedactsProjectFrame(t *testing.T) {
	samples := []schema.Sample{
		sampleWithStack("zz-test-private-proj", "00", "skill:build", "main", "claude-haiku-4-5"),
	}
	ScrubFrames(samples, []string{"zz-test"})

	if got := samples[0].Stack[0]; got != "(redacted)" {
		t.Errorf("project frame = %q, want %q", got, "(redacted)")
	}
	// Non-matching frames are untouched.
	if got := samples[0].Stack[2]; got != "skill:build" {
		t.Errorf("skill frame = %q, want unchanged %q", got, "skill:build")
	}
}

func TestScrubFramesEmptyDenylistLeavesFramesUnchanged(t *testing.T) {
	orig := []string{"zz-test-private-proj", "00", "skill:zz-test-private", "main", "claude-haiku-4-5"}
	samples := []schema.Sample{sampleWithStack(orig...)}
	before := emitJSONL(t, samples)

	ScrubFrames(samples, nil)

	if after := emitJSONL(t, samples); after != before {
		t.Errorf("empty denylist changed output:\nbefore=%s\nafter =%s", before, after)
	}
}

func TestLoadDenylistReadsLinesAndSkipsBlanks(t *testing.T) {
	dir := t.TempDir()
	path := filepath.Join(dir, "frame-denylist")
	if err := os.WriteFile(path, []byte("zz-test\n\n  spaced-secret  \n\n"), 0o600); err != nil {
		t.Fatal(err)
	}
	denied, err := LoadDenylist(path)
	if err != nil {
		t.Fatalf("LoadDenylist: %v", err)
	}
	want := []string{"zz-test", "spaced-secret"}
	if len(denied) != len(want) {
		t.Fatalf("denied = %v, want %v", denied, want)
	}
	for i := range want {
		if denied[i] != want[i] {
			t.Errorf("denied[%d] = %q, want %q", i, denied[i], want[i])
		}
	}
}

func TestLoadDenylistMissingFileIsNoDenylist(t *testing.T) {
	denied, err := LoadDenylist(filepath.Join(t.TempDir(), "does-not-exist"))
	if err != nil {
		t.Fatalf("missing file should not error, got %v", err)
	}
	if denied != nil {
		t.Errorf("missing file should yield nil denylist, got %v", denied)
	}
}
