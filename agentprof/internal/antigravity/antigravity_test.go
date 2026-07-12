package antigravity

import (
	"os"
	"path/filepath"
	"testing"
	"time"
)

// Confirmed ground-truth values decoded from the committed fixture
// testdata/conversations/d147c9da-7c14-4e02-a386-156a72b7bf99.db (see
// testdata/README.md). Verified this task via protoc --decode_raw: the
// gen_metadata `data` blob wraps the generation submessage in top-level
// field 1, so every field the SPEC numbers (4 tokens, 9.4 Timestamp, 21
// display string, 20 map) lives one level down at 1->N.
const (
	fixtureCascadeID    = "d147c9da-7c14-4e02-a386-156a72b7bf99"
	fixtureDBFile       = "d147c9da-7c14-4e02-a386-156a72b7bf99.db"
	fixtureTrajectoryID = "2d277f57-be61-4705-8581-22e7af27646c"
	fixtureModel        = "Gemini 3.5 Flash (Medium)"
	// trajectory_metadata_blob field 18 (project label) is a per-project
	// UUID here because the fixture session was captured with --new-project;
	// the extraction rule prefers field 18 when present and non-empty.
	fixtureProject     = "eda80a54-7a3d-4d1d-a0f7-a33d5c18ae4c"
	fixtureInputTokens = 17234 // gen field 1->4 sub-field 2
	fixtureOutputTok   = 71    // gen field 1->4 sub-field 3
	// PriceGemini("Gemini 3.5 Flash (Medium)"): 17234*0.30 + 71*2.50 = 5347.7
	fixtureCostMicroUSD = 5348
)

// fixtureTime is 1->9->4 {1: 1783813771 seconds, 2: 429751000 nanos}.
var fixtureTime = time.Unix(1783813771, 429751000).UTC()

// beforeFixture is a cutoff comfortably earlier than the fixture generation
// time, so the single fixture row is always in-window.
var beforeFixture = time.Date(2020, 1, 1, 0, 0, 0, 0, time.UTC)

const realFixtureDB = "testdata/conversations/d147c9da-7c14-4e02-a386-156a72b7bf99.db"

// stagedFixtureDir copies the committed real fixture into a fresh temp
// <dir>/conversations/ and returns <dir>. Tests read the copy rather than the
// tracked file so that SQLite's read-only WAL sidecars (-wal/-shm, created
// because the committed fixture is a WAL-mode db) never dirty the tracked
// testdata/ directory. The copy is byte-identical, so this still exercises
// Collect against the committed fixture's real bytes.
func stagedFixtureDir(t *testing.T) string {
	t.Helper()
	dir := t.TempDir()
	conv := filepath.Join(dir, "conversations")
	if err := os.MkdirAll(conv, 0o755); err != nil {
		t.Fatal(err)
	}
	copyFile(t, realFixtureDB, filepath.Join(conv, filepath.Base(realFixtureDB)))
	return dir
}

func TestCollectReturnsSampleFromFixture(t *testing.T) {
	samples, skipped, err := Collect(stagedFixtureDir(t), beforeFixture)
	if err != nil {
		t.Fatalf("Collect returned error: %v", err)
	}
	if skipped != 0 {
		t.Errorf("skipped = %d, want 0", skipped)
	}
	if len(samples) != 1 {
		t.Fatalf("len(samples) = %d, want 1", len(samples))
	}
	if !samples[0].Time.Equal(fixtureTime) {
		t.Errorf("Time = %v, want %v", samples[0].Time, fixtureTime)
	}
	// session label equals the .db basename (== cascade_id).
	if got := samples[0].Labels["session"]; got != fixtureCascadeID {
		t.Errorf("Labels[session] = %q, want %q (the .db basename)", got, fixtureCascadeID)
	}
}

func TestCollectStackProjectFrame(t *testing.T) {
	samples, _, err := Collect(stagedFixtureDir(t), beforeFixture)
	if err != nil || len(samples) != 1 {
		t.Fatalf("Collect: samples=%d err=%v", len(samples), err)
	}
	want := []string{fixtureProject, "antigravity", fixtureModel}
	got := samples[0].Stack
	if len(got) != len(want) {
		t.Fatalf("Stack = %v, want %v", got, want)
	}
	for i := range want {
		if got[i] != want[i] {
			t.Errorf("Stack[%d] = %q, want %q", i, got[i], want[i])
		}
	}
}

// The fallback path (field 18 empty -> workspace-URI basename) is not
// exercised by the fixture, whose field 18 is a non-empty UUID. Cover it
// directly against a hand-built trajectory_metadata_blob so a broken
// fallback can't ship untested.
func TestProjectFrameFallsBackToWorkspaceBasename(t *testing.T) {
	// outer field 1 = submessage {1: workspace file:// URI}; field 18 empty.
	inner := strField(1, "file:///home/me/projects/my-repo")
	blob := lenField(1, inner)
	blob = append(blob, strField(18, "")...) // present but empty -> skipped
	got := projectFromTrajectoryBlob(blob)
	if got != "my-repo" {
		t.Errorf("project = %q, want %q (workspace basename fallback)", got, "my-repo")
	}
}

func TestProjectFramePrefersField18WhenNonEmpty(t *testing.T) {
	inner := strField(1, "file:///home/me/projects/my-repo")
	blob := lenField(1, inner)
	blob = append(blob, strField(18, "default-cli-project")...)
	got := projectFromTrajectoryBlob(blob)
	if got != "default-cli-project" {
		t.Errorf("project = %q, want %q (field 18 preferred)", got, "default-cli-project")
	}
}

func TestCollectTokenMappingAndCost(t *testing.T) {
	samples, _, err := Collect(stagedFixtureDir(t), beforeFixture)
	if err != nil || len(samples) != 1 {
		t.Fatalf("Collect: samples=%d err=%v", len(samples), err)
	}
	v := samples[0].Values
	if v["input_tokens"] != fixtureInputTokens {
		t.Errorf("input_tokens = %d, want %d", v["input_tokens"], fixtureInputTokens)
	}
	if v["output_tokens"] != fixtureOutputTok {
		t.Errorf("output_tokens = %d, want %d", v["output_tokens"], fixtureOutputTok)
	}
	if v["calls"] != 1 {
		t.Errorf("calls = %d, want 1", v["calls"])
	}
	if v["cost_microusd"] != fixtureCostMicroUSD {
		t.Errorf("cost_microusd = %d, want %d", v["cost_microusd"], fixtureCostMicroUSD)
	}
	// README cannot confidently identify a cache-read sub-field (6/9/10 are
	// unidentified), so cache_read_tokens must be left OUT rather than guessed.
	if _, present := v["cache_read_tokens"]; present {
		t.Errorf("cache_read_tokens present (%d); it must be omitted — the README cannot confirm which sub-field it is", v["cache_read_tokens"])
	}
}

func TestCollectLabels(t *testing.T) {
	samples, _, err := Collect(stagedFixtureDir(t), beforeFixture)
	if err != nil || len(samples) != 1 {
		t.Fatalf("Collect: samples=%d err=%v", len(samples), err)
	}
	l := samples[0].Labels
	want := map[string]string{
		"source":        "antigravity",
		"session":       fixtureCascadeID,
		"trajectory_id": fixtureTrajectoryID,
		"model_raw":     fixtureModel,
		"db_file":       fixtureDBFile,
	}
	for k, w := range want {
		if l[k] != w {
			t.Errorf("Labels[%q] = %q, want %q", k, l[k], w)
		}
	}
	// model_raw must be byte-identical to the Stack model leaf and to what
	// PriceGemini is keyed on.
	if l["model_raw"] != samples[0].Stack[len(samples[0].Stack)-1] {
		t.Errorf("model_raw %q != Stack model leaf %q", l["model_raw"], samples[0].Stack[len(samples[0].Stack)-1])
	}
}

// copyFile copies src to dst byte-for-byte.
func copyFile(t *testing.T, src, dst string) {
	t.Helper()
	b, err := os.ReadFile(src)
	if err != nil {
		t.Fatalf("read %s: %v", src, err)
	}
	if err := os.WriteFile(dst, b, 0o644); err != nil {
		t.Fatalf("write %s: %v", dst, err)
	}
}

func TestCollectSkipsCorruptFixtureAndCounts(t *testing.T) {
	// Stage the committed corrupted-copy fixture into a temp <dir>/conversations/
	// so Collect's <dir>/conversations/*.db glob finds it. Its gen_metadata
	// blob is unparseable, so the row is skipped, not fatal.
	tmp := t.TempDir()
	conv := filepath.Join(tmp, "conversations")
	if err := os.MkdirAll(conv, 0o755); err != nil {
		t.Fatal(err)
	}
	copyFile(t,
		"testdata/conversations-corrupt/d147c9da-7c14-4e02-a386-156a72b7bf99-corrupt.db",
		filepath.Join(conv, "corrupt.db"))

	samples, skipped, err := Collect(tmp, beforeFixture)
	if err != nil {
		t.Fatalf("Collect returned error on corrupt fixture: %v (must skip, not error)", err)
	}
	if len(samples) != 0 {
		t.Errorf("len(samples) = %d, want 0 (corrupt blob yields no sample)", len(samples))
	}
	if skipped != 1 {
		t.Errorf("skipped = %d, want 1 (the unparseable row)", skipped)
	}
}

func TestCollectValidAndCorruptTogether(t *testing.T) {
	// A dir holding one good and one corrupt db yields one sample and one skip.
	tmp := t.TempDir()
	conv := filepath.Join(tmp, "conversations")
	if err := os.MkdirAll(conv, 0o755); err != nil {
		t.Fatal(err)
	}
	copyFile(t,
		"testdata/conversations/d147c9da-7c14-4e02-a386-156a72b7bf99.db",
		filepath.Join(conv, "a-good.db"))
	copyFile(t,
		"testdata/conversations-corrupt/d147c9da-7c14-4e02-a386-156a72b7bf99-corrupt.db",
		filepath.Join(conv, "z-corrupt.db"))

	samples, skipped, err := Collect(tmp, beforeFixture)
	if err != nil {
		t.Fatalf("Collect error: %v", err)
	}
	if len(samples) != 1 {
		t.Errorf("len(samples) = %d, want 1", len(samples))
	}
	if skipped != 1 {
		t.Errorf("skipped = %d, want 1", skipped)
	}
}

func TestCollectEmptyDirReturnsZero(t *testing.T) {
	samples, skipped, err := Collect(t.TempDir(), beforeFixture)
	if err != nil {
		t.Fatalf("Collect on empty dir returned error: %v", err)
	}
	if len(samples) != 0 || skipped != 0 {
		t.Errorf("empty dir: samples=%d skipped=%d, want 0/0", len(samples), skipped)
	}
}

func TestCollectNonexistentDirReturnsZero(t *testing.T) {
	samples, skipped, err := Collect(filepath.Join(t.TempDir(), "does-not-exist"), beforeFixture)
	if err != nil {
		t.Fatalf("Collect on nonexistent dir returned error: %v", err)
	}
	if len(samples) != 0 || skipped != 0 {
		t.Errorf("nonexistent dir: samples=%d skipped=%d, want 0/0", len(samples), skipped)
	}
}

func TestCollectCutoffExcludesOldRows(t *testing.T) {
	// A cutoff after the fixture generation time excludes the row (not a skip).
	after := fixtureTime.Add(time.Hour)
	samples, skipped, err := Collect(stagedFixtureDir(t), after)
	if err != nil {
		t.Fatalf("Collect error: %v", err)
	}
	if len(samples) != 0 {
		t.Errorf("len(samples) = %d, want 0 (row is before cutoff)", len(samples))
	}
	if skipped != 0 {
		t.Errorf("skipped = %d, want 0 (out-of-window is a filter, not a skip)", skipped)
	}
}
