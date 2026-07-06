package claude_test

import (
	"crypto/sha256"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"reflect"
	"sort"
	"strings"
	"testing"
	"time"

	"github.com/sticklane/agentprof/internal/claude"
	"github.com/sticklane/agentprof/internal/schema"
)

const fixtureDir = "../../testdata/claude-dir"

// anyCutoff includes every session regardless of file mtimes.
var anyCutoff = time.Time{}

func collectFixture(t *testing.T) ([]schema.Sample, int) {
	t.Helper()
	samples, _, skipped, err := claude.Collect(fixtureDir, anyCutoff)
	if err != nil {
		t.Fatalf("Collect: %v", err)
	}
	return samples, skipped
}

// findByStack returns the samples whose stack equals want.
func findByStack(samples []schema.Sample, want []string) []schema.Sample {
	var out []schema.Sample
	for _, s := range samples {
		if reflect.DeepEqual(s.Stack, want) {
			out = append(out, s)
		}
	}
	return out
}

func TestCollectProducesOneSamplePerDedupedResponse(t *testing.T) {
	samples, skipped := collectFixture(t)

	// 10 deduped model-call samples + 3 tool: samples (toolu_W -> tool:Workflow,
	// toolu_A and toolu_WS unresolved -> tool:(pending)) added by task 01.
	if len(samples) != 13 {
		t.Errorf("got %d samples, want 13", len(samples))
	}
	if skipped != 1 {
		t.Errorf("got %d skipped lines, want 1 (the truncated final line)", skipped)
	}
}

func TestCollectDedupsRepeatedMessageIDCountingUsageOnce(t *testing.T) {
	samples, _ := collectFixture(t)

	// msg_a2 appears on 3 identical lines; it must yield exactly one sample.
	got := findByStack(samples, []string{"proj", "t02 · /parallel specs/agentprof", "(no skill)", "main", "claude-fable-5"})
	if len(got) != 1 {
		t.Fatalf("got %d samples for repeated msg_a2 stack, want 1", len(got))
	}
	if got[0].Values["input_tokens"] != 200 || got[0].Values["output_tokens"] != 20 {
		t.Errorf("msg_a2 values = %v, want input 200 / output 20", got[0].Values)
	}
}

func TestCollectDedupsByRequestIDWhenMessageIDMissing(t *testing.T) {
	samples, _ := collectFixture(t)

	// req-fallback-1 appears on 2 identical lines without message.id.
	got := findByStack(samples, []string{"beta", "t01 · hello", "(no skill)", "main", "claude-sonnet-4-5"})
	if len(got) != 1 {
		t.Fatalf("got %d samples for requestId-fallback stack, want 1", len(got))
	}
	if got[0].Values["input_tokens"] != 600 || got[0].Values["output_tokens"] != 60 {
		t.Errorf("req-fallback values = %v, want input 600 / output 60", got[0].Values)
	}
}

func TestCollectCountsEachUsageLineWhenBothDedupKeysMissing(t *testing.T) {
	dir := t.TempDir()
	proj := filepath.Join(dir, "projects", "-z-app")
	if err := os.MkdirAll(proj, 0o755); err != nil {
		t.Fatal(err)
	}
	line := `{"type":"assistant","timestamp":"2026-07-01T09:00:00Z","cwd":"/z/app","sessionId":"sess-z","message":{"model":"claude-fable-5","usage":{"input_tokens":10,"output_tokens":1}}}`
	content := line + "\n" + line + "\n"
	if err := os.WriteFile(filepath.Join(proj, "sess-z.jsonl"), []byte(content), 0o644); err != nil {
		t.Fatal(err)
	}

	samples, _, skipped, err := claude.Collect(dir, anyCutoff)
	if err != nil {
		t.Fatalf("Collect: %v", err)
	}
	if skipped != 0 {
		t.Errorf("skipped = %d, want 0", skipped)
	}
	if len(samples) != 2 {
		t.Errorf("got %d samples, want 2 (no dedup key means every usage line counts)", len(samples))
	}
}

func TestCollectBuildsExpectedStacksIncludingNestedWorkflowAgent(t *testing.T) {
	samples, _ := collectFixture(t)

	data, err := os.ReadFile(fixtureDir + ".expected.json")
	if err != nil {
		t.Fatal(err)
	}
	var expected struct {
		Stacks map[string][]string `json:"stacks"`
	}
	if err := json.Unmarshal(data, &expected); err != nil {
		t.Fatal(err)
	}

	want := map[string]bool{}
	for _, stack := range expected.Stacks {
		want[strings.Join(stack, " / ")] = true
	}
	got := map[string]bool{}
	for _, s := range samples {
		got[strings.Join(s.Stack, " / ")] = true
	}
	if !reflect.DeepEqual(got, want) {
		t.Errorf("stack sets differ:\ngot  %v\nwant %v", keys(got), keys(want))
	}
}

func TestCollectFallsBackToMungedDirNameWhenNoCwd(t *testing.T) {
	dir := t.TempDir()
	proj := filepath.Join(dir, "projects", "-z-app")
	if err := os.MkdirAll(proj, 0o755); err != nil {
		t.Fatal(err)
	}
	line := `{"type":"assistant","timestamp":"2026-07-01T09:00:00Z","sessionId":"sess-z","message":{"id":"m1","model":"claude-fable-5","usage":{"input_tokens":10,"output_tokens":1}}}`
	if err := os.WriteFile(filepath.Join(proj, "sess-z.jsonl"), []byte(line+"\n"), 0o644); err != nil {
		t.Fatal(err)
	}

	samples, _, _, err := claude.Collect(dir, anyCutoff)
	if err != nil {
		t.Fatalf("Collect: %v", err)
	}
	if len(samples) != 1 {
		t.Fatalf("got %d samples, want 1", len(samples))
	}
	if samples[0].Stack[0] != "-z-app" {
		t.Errorf("project frame = %q, want munged dir name %q", samples[0].Stack[0], "-z-app")
	}
}

func TestCollectSetsValuesCostLabelsAndTimeFromLine(t *testing.T) {
	samples, _ := collectFixture(t)

	got := findByStack(samples, []string{"proj", "t01 · start", "skill:build", "main", "claude-fable-5"})
	if len(got) != 1 {
		t.Fatalf("got %d samples for msg_a1 stack, want 1", len(got))
	}
	s := got[0]

	wantValues := map[string]int64{
		"input_tokens":       100,
		"output_tokens":      10,
		"cache_read_tokens":  50,
		"cache_write_tokens": 20,
		// 100*10 + 10*50 + 50*1 + 15*12.50 + 5*20 = 1837.5 -> 1838
		// (5m/1h sub-fields present, so they price separately).
		"cost_microusd": 1838,
		"calls":         1,
	}
	if !reflect.DeepEqual(s.Values, wantValues) {
		t.Errorf("msg_a1 values = %v, want %v", s.Values, wantValues)
	}
	wantTime := time.Date(2026, 7, 1, 10, 1, 0, 0, time.UTC)
	if !s.Time.Equal(wantTime) {
		t.Errorf("msg_a1 time = %v, want %v", s.Time, wantTime)
	}
	wantLabels := map[string]string{"source": "claude-code", "session": "sess-0001", "turn": "01"}
	if !reflect.DeepEqual(s.Labels, wantLabels) {
		t.Errorf("msg_a1 labels = %v, want %v", s.Labels, wantLabels)
	}
}

func TestCollectLabelsUnknownModelSamplesPricedFalse(t *testing.T) {
	samples, _ := collectFixture(t)

	unpriced := 0
	for _, s := range samples {
		if s.Labels["priced"] == "false" {
			unpriced++
			if s.Values["cost_microusd"] != 0 {
				t.Errorf("unpriced sample %v has cost %d, want 0", s.Stack, s.Values["cost_microusd"])
			}
		}
	}
	if unpriced != 2 {
		t.Errorf("got %d priced=false samples, want 2 (mystery-model-9 and <synthetic>)", unpriced)
	}
}

func TestCollectTotalsMatchExpectedFixtureData(t *testing.T) {
	samples, _ := collectFixture(t)

	data, err := os.ReadFile(fixtureDir + ".expected.json")
	if err != nil {
		t.Fatal(err)
	}
	var expected struct {
		TotalInputTokens     int64 `json:"total_input_tokens"`
		TotalOutputTokens    int64 `json:"total_output_tokens"`
		TotalCacheReadTokens int64 `json:"total_cache_read_tokens"`
		TotalCacheWrite      int64 `json:"total_cache_write_tokens"`
		TotalCostMicroUSD    int64 `json:"total_cost_microusd"`
		TotalDurationMs      int64 `json:"total_duration_ms"`
	}
	if err := json.Unmarshal(data, &expected); err != nil {
		t.Fatal(err)
	}

	totals := map[string]int64{}
	for _, s := range samples {
		for k, v := range s.Values {
			totals[k] += v
		}
	}
	want := map[string]int64{
		"input_tokens":       expected.TotalInputTokens,
		"output_tokens":      expected.TotalOutputTokens,
		"cache_read_tokens":  expected.TotalCacheReadTokens,
		"cache_write_tokens": expected.TotalCacheWrite,
		"cost_microusd":      expected.TotalCostMicroUSD,
		"calls":              10,
		"duration_ms":        expected.TotalDurationMs,
	}
	if !reflect.DeepEqual(totals, want) {
		t.Errorf("totals = %v, want %v", totals, want)
	}
}

func TestCollectExcludesSessionsWithAllFilesOlderThanCutoff(t *testing.T) {
	dir := copyFixture(t)
	old := time.Now().Add(-90 * 24 * time.Hour)
	fresh := time.Now()
	chtimesSession(t, dir, "-x-proj", "sess-0001", old)
	chtimesSession(t, dir, "-y-beta", "sess-0002", fresh)

	cutoff := time.Now().Add(-30 * 24 * time.Hour)
	samples, _, _, err := claude.Collect(dir, cutoff)
	if err != nil {
		t.Fatalf("Collect: %v", err)
	}
	if len(samples) != 4 {
		t.Fatalf("got %d samples, want 4 (only sess-0002 in window)", len(samples))
	}
	for _, s := range samples {
		if s.Labels["session"] != "sess-0002" {
			t.Errorf("out-of-window sample leaked: %v", s.Stack)
		}
	}
}

func TestCollectFreshSubagentFilePullsWholeSessionIntoWindow(t *testing.T) {
	dir := copyFixture(t)
	old := time.Now().Add(-90 * 24 * time.Hour)
	chtimesSession(t, dir, "-x-proj", "sess-0001", old)
	chtimesSession(t, dir, "-y-beta", "sess-0002", old)
	// Only the nested workflow subagent file is fresh; the whole sess-0001
	// session must come back in-window, main transcript included.
	nested := filepath.Join(dir, "projects", "-x-proj", "sess-0001",
		"subagents", "workflows", "wf_test", "agent-W.jsonl")
	if err := os.Chtimes(nested, time.Now(), time.Now()); err != nil {
		t.Fatal(err)
	}

	cutoff := time.Now().Add(-30 * 24 * time.Hour)
	samples, _, _, err := claude.Collect(dir, cutoff)
	if err != nil {
		t.Fatalf("Collect: %v", err)
	}
	if len(samples) != 9 {
		t.Fatalf("got %d samples, want 9 (all of sess-0001 incl. 3 tool: samples, none of sess-0002)", len(samples))
	}
	sessions := map[string]bool{}
	frames := map[string]bool{}
	for _, s := range samples {
		sessions[s.Labels["session"]] = true
		for _, f := range s.Stack {
			frames[f] = true
		}
	}
	if !reflect.DeepEqual(sessions, map[string]bool{"sess-0001": true}) {
		t.Errorf("sessions in window = %v, want only sess-0001", keys(sessions))
	}
	if !frames["t02 · /parallel specs/agentprof"] {
		t.Error("fresh subagent must pull the session MAIN transcript in-window too")
	}
}

func TestCollectSkipsMalformedLinesAndEmptyTranscriptsWithoutError(t *testing.T) {
	dir := t.TempDir()
	proj := filepath.Join(dir, "projects", "-z-app")
	if err := os.MkdirAll(proj, 0o755); err != nil {
		t.Fatal(err)
	}
	good := `{"type":"assistant","timestamp":"2026-07-01T09:00:00Z","cwd":"/z/app","sessionId":"sess-z","message":{"id":"m1","model":"claude-fable-5","usage":{"input_tokens":10,"output_tokens":1}}}`
	content := "not json at all\n" + good + "\n" + `{"type":"assistant","trunca`
	if err := os.WriteFile(filepath.Join(proj, "sess-z.jsonl"), []byte(content), 0o644); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(filepath.Join(proj, "sess-empty.jsonl"), nil, 0o644); err != nil {
		t.Fatal(err)
	}

	samples, _, skipped, err := claude.Collect(dir, anyCutoff)
	if err != nil {
		t.Fatalf("Collect must not fail on garbage: %v", err)
	}
	if len(samples) != 1 {
		t.Errorf("got %d samples, want 1", len(samples))
	}
	if skipped != 2 {
		t.Errorf("skipped = %d, want 2 (bad JSON + truncated line; empty file counts nothing)", skipped)
	}
}

func TestCollectIsReadOnly(t *testing.T) {
	before := hashTree(t, fixtureDir)
	collectFixture(t)
	after := hashTree(t, fixtureDir)
	if before != after {
		t.Error("fixture tree changed during Collect; reads must be strictly read-only")
	}
}

func TestCollectIsDeterministicAcrossRuns(t *testing.T) {
	first, _ := collectFixture(t)
	second, _ := collectFixture(t)
	if !reflect.DeepEqual(first, second) {
		t.Error("two Collect runs over the same tree returned different samples")
	}
}

// writeMain writes a main transcript for session sess-z under a temp claude
// dir and returns the dir.
func writeMain(t *testing.T, lines ...string) string {
	t.Helper()
	dir := t.TempDir()
	proj := filepath.Join(dir, "projects", "-z-app")
	if err := os.MkdirAll(proj, 0o755); err != nil {
		t.Fatal(err)
	}
	content := strings.Join(lines, "\n") + "\n"
	if err := os.WriteFile(filepath.Join(proj, "sess-z.jsonl"), []byte(content), 0o644); err != nil {
		t.Fatal(err)
	}
	return dir
}

func assistantLine(msgID string) string {
	return `{"type":"assistant","timestamp":"2026-07-01T09:05:00Z","cwd":"/z/app","sessionId":"sess-z","message":{"id":"` + msgID + `","model":"claude-fable-5","usage":{"input_tokens":10,"output_tokens":1}}}`
}

func assistantLineWithSkill(msgID, skill string) string {
	return `{"type":"assistant","timestamp":"2026-07-01T09:05:00Z","cwd":"/z/app","sessionId":"sess-z","attributionSkill":"` + skill + `","message":{"id":"` + msgID + `","model":"claude-fable-5","usage":{"input_tokens":10,"output_tokens":1}}}`
}

// TestCollectSkillFrameCollapsesNamespacedAndBareIntoOneFrame covers R1:
// a leading `<plugin>:` namespace is stripped so `agentic:build` and bare
// `build` land in the same `skill:build` frame, while lines with no
// attributionSkill keep the unchanged `(no skill)` frame.
func TestCollectSkillFrameCollapsesNamespacedAndBareIntoOneFrame(t *testing.T) {
	dir := writeMain(t,
		assistantLineWithSkill("m1", "agentic:build"),
		assistantLineWithSkill("m2", "build"),
		assistantLine("m3"),
	)

	samples, _, _, err := claude.Collect(dir, anyCutoff)
	if err != nil {
		t.Fatalf("Collect: %v", err)
	}
	if len(samples) != 3 {
		t.Fatalf("got %d samples, want 3", len(samples))
	}
	if got := samples[0].Stack[2]; got != "skill:build" {
		t.Errorf("namespaced attributionSkill frame = %q, want %q", got, "skill:build")
	}
	if got := samples[1].Stack[2]; got != "skill:build" {
		t.Errorf("bare attributionSkill frame = %q, want %q", got, "skill:build")
	}
	if got := samples[2].Stack[2]; got != "(no skill)" {
		t.Errorf("absent attributionSkill frame = %q, want %q", got, "(no skill)")
	}
}

func TestCollectAssignsSyntheticTurnZeroToSamplesBeforeFirstPrompt(t *testing.T) {
	dir := writeMain(t,
		assistantLine("m1"),
		`{"type":"user","timestamp":"2026-07-01T09:06:00Z","cwd":"/z/app","sessionId":"sess-z","message":{"role":"user","content":"hi there"}}`,
		assistantLine("m2"),
	)

	samples, _, _, err := claude.Collect(dir, anyCutoff)
	if err != nil {
		t.Fatalf("Collect: %v", err)
	}
	if len(samples) != 2 {
		t.Fatalf("got %d samples, want 2", len(samples))
	}
	if got := samples[0].Stack[1]; got != "t00 · (before first prompt)" {
		t.Errorf("pre-prompt sample turn frame = %q, want synthetic t00", got)
	}
	if got := samples[0].Labels["turn"]; got != "00" {
		t.Errorf("pre-prompt sample turn label = %q, want %q", got, "00")
	}
	if got := samples[1].Stack[1]; got != "t01 · hi there" {
		t.Errorf("post-prompt sample turn frame = %q, want %q", got, "t01 · hi there")
	}
	if got := samples[1].Labels["turn"]; got != "01" {
		t.Errorf("post-prompt sample turn label = %q, want %q", got, "01")
	}
}

func TestCollectDoesNotOpenTurnsForMetaSidechainToolResultOrExcludedLines(t *testing.T) {
	dir := writeMain(t,
		`{"type":"user","timestamp":"2026-07-01T09:00:00Z","cwd":"/z/app","sessionId":"sess-z","isMeta":true,"message":{"role":"user","content":"meta note"}}`,
		`{"type":"user","timestamp":"2026-07-01T09:00:01Z","cwd":"/z/app","sessionId":"sess-z","isSidechain":true,"message":{"role":"user","content":"sidechain prompt"}}`,
		`{"type":"user","timestamp":"2026-07-01T09:00:02Z","cwd":"/z/app","sessionId":"sess-z","message":{"role":"user","content":[{"type":"tool_result","tool_use_id":"tu1","content":"ok"}]}}`,
		`{"type":"user","timestamp":"2026-07-01T09:00:03Z","cwd":"/z/app","sessionId":"sess-z","message":{"role":"user","content":"<task-notification>agent done</task-notification>"}}`,
		`{"type":"user","timestamp":"2026-07-01T09:00:04Z","cwd":"/z/app","sessionId":"sess-z","message":{"role":"user","content":"  [Request interrupted by user]"}}`,
		`{"type":"user","timestamp":"2026-07-01T09:00:05Z","cwd":"/z/app","sessionId":"sess-z","message":{"role":"user","content":"<bash-stdout>out</bash-stdout>"}}`,
		`{"type":"user","timestamp":"2026-07-01T09:00:06Z","cwd":"/z/app","sessionId":"sess-z","message":{"role":"user","content":""}}`,
		assistantLine("m1"),
	)

	samples, _, _, err := claude.Collect(dir, anyCutoff)
	if err != nil {
		t.Fatalf("Collect: %v", err)
	}
	if len(samples) != 1 {
		t.Fatalf("got %d samples, want 1", len(samples))
	}
	if got := samples[0].Stack[1]; got != "t00 · (before first prompt)" {
		t.Errorf("turn frame = %q, want synthetic t00 (no line above may open a turn)", got)
	}
}

func TestCollectTruncatesTurnSnippetToFortyRunes(t *testing.T) {
	prompt := strings.Repeat("é", 45)
	dir := writeMain(t,
		`{"type":"user","timestamp":"2026-07-01T09:00:00Z","cwd":"/z/app","sessionId":"sess-z","message":{"role":"user","content":"`+prompt+`"}}`,
		assistantLine("m1"),
	)

	samples, _, _, err := claude.Collect(dir, anyCutoff)
	if err != nil {
		t.Fatalf("Collect: %v", err)
	}
	if len(samples) != 1 {
		t.Fatalf("got %d samples, want 1", len(samples))
	}
	want := "t01 · " + strings.Repeat("é", 40) + "…"
	if got := samples[0].Stack[1]; got != want {
		t.Errorf("turn frame = %q, want %q (40-rune truncation)", got, want)
	}
}

func TestCollectMarksSubagentWithUnresolvableToolUseIDUnlinked(t *testing.T) {
	dir := writeMain(t,
		`{"type":"user","timestamp":"2026-07-01T09:00:00Z","cwd":"/z/app","sessionId":"sess-z","message":{"role":"user","content":"hi"}}`,
		assistantLine("m1"),
	)
	sub := filepath.Join(dir, "projects", "-z-app", "sess-z", "subagents")
	if err := os.MkdirAll(sub, 0o755); err != nil {
		t.Fatal(err)
	}
	agent := `{"type":"assistant","timestamp":"2026-07-01T09:10:00Z","cwd":"/z/app","sessionId":"sess-z","message":{"id":"m_sub","model":"claude-haiku-4-5","usage":{"input_tokens":5,"output_tokens":1}}}`
	if err := os.WriteFile(filepath.Join(sub, "agent-X.jsonl"), []byte(agent+"\n"), 0o644); err != nil {
		t.Fatal(err)
	}
	meta := `{"agentId":"agent-X","agentType":"scout","toolUseId":"toolu_nowhere","spawnDepth":1}`
	if err := os.WriteFile(filepath.Join(sub, "agent-X.meta.json"), []byte(meta+"\n"), 0o644); err != nil {
		t.Fatal(err)
	}

	samples, _, _, err := claude.Collect(dir, anyCutoff)
	if err != nil {
		t.Fatalf("Collect: %v", err)
	}
	got := findByStack(samples, []string{"app", "(unlinked)", "agent:scout", "claude-haiku-4-5"})
	if len(got) != 1 {
		t.Fatalf("got %d unlinked samples, want 1; all samples: %v", len(got), stacks(samples))
	}
	if _, ok := got[0].Labels["turn"]; ok {
		t.Errorf("unlinked sample must carry no turn label, got %q", got[0].Labels["turn"])
	}
}

func TestCollectInheritsTurnLabelThroughSpawnChain(t *testing.T) {
	samples, _ := collectFixture(t)

	// agent-WS is depth-2 (main -> run-linked agent-W -> agent-WS), spawned
	// inside turn 01; the wf: frame arrives once, via agent-W's prefix.
	deep := findByStack(samples, []string{"proj", "t01 · start", "skill:build", "main",
		"wf:test-flow", "agent:workflow-subagent", "agent:scout", "claude-haiku-4-5"})
	if len(deep) != 1 {
		t.Fatalf("got %d depth-2 samples, want 1; all samples: %v", len(deep), stacks(samples))
	}
	if got := deep[0].Labels["turn"]; got != "01" {
		t.Errorf("depth-2 sample turn label = %q, want inherited %q", got, "01")
	}
}

func stacks(samples []schema.Sample) []string {
	var out []string
	for _, s := range samples {
		out = append(out, strings.Join(s.Stack, " / "))
	}
	return out
}

// copyFixture copies testdata/claude-dir into a temp dir so tests can adjust
// mtimes without touching the committed fixture.
func copyFixture(t *testing.T) string {
	t.Helper()
	dst := t.TempDir()
	err := filepath.WalkDir(fixtureDir, func(path string, d os.DirEntry, err error) error {
		if err != nil {
			return err
		}
		rel, err := filepath.Rel(fixtureDir, path)
		if err != nil {
			return err
		}
		target := filepath.Join(dst, rel)
		if d.IsDir() {
			return os.MkdirAll(target, 0o755)
		}
		data, err := os.ReadFile(path)
		if err != nil {
			return err
		}
		return os.WriteFile(target, data, 0o644)
	})
	if err != nil {
		t.Fatal(err)
	}
	return dst
}

// chtimesSession sets the mtime of a session's main transcript and every file
// under its session directory.
func chtimesSession(t *testing.T, dir, projDir, sessionID string, mtime time.Time) {
	t.Helper()
	main := filepath.Join(dir, "projects", projDir, sessionID+".jsonl")
	if err := os.Chtimes(main, mtime, mtime); err != nil {
		t.Fatal(err)
	}
	sessDir := filepath.Join(dir, "projects", projDir, sessionID)
	if _, err := os.Stat(sessDir); os.IsNotExist(err) {
		return // session has no subagent directory
	}
	err := filepath.WalkDir(sessDir, func(path string, d os.DirEntry, err error) error {
		if err != nil || d.IsDir() {
			return err
		}
		return os.Chtimes(path, mtime, mtime)
	})
	if err != nil {
		t.Fatal(err)
	}
}

func hashTree(t *testing.T, dir string) string {
	t.Helper()
	h := sha256.New()
	err := filepath.WalkDir(dir, func(path string, d os.DirEntry, err error) error {
		if err != nil || d.IsDir() {
			return err
		}
		data, err := os.ReadFile(path)
		if err != nil {
			return err
		}
		fmt.Fprintf(h, "%s %x\n", path, sha256.Sum256(data))
		return nil
	})
	if err != nil {
		t.Fatal(err)
	}
	return fmt.Sprintf("%x", h.Sum(nil))
}

func keys(m map[string]bool) []string {
	out := make([]string, 0, len(m))
	for k := range m {
		out = append(out, k)
	}
	sort.Strings(out)
	return out
}
