package main

import (
	"encoding/json"
	"maps"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

func generateInto(t *testing.T) string {
	t.Helper()
	root := t.TempDir()
	if err := generate(root); err != nil {
		t.Fatalf("generate: %v", err)
	}
	return root
}

func TestGenerateCreatesTwoProjectDirs(t *testing.T) {
	root := generateInto(t)

	entries, err := os.ReadDir(filepath.Join(root, "claude-dir", "projects"))
	if err != nil {
		t.Fatalf("read projects dir: %v", err)
	}
	if len(entries) != 2 {
		t.Fatalf("want 2 project dirs, got %d", len(entries))
	}
	for _, e := range entries {
		if !e.IsDir() {
			t.Errorf("projects/%s is not a directory", e.Name())
		}
	}
}

func TestGenerateCreatesMetalessSubagentB(t *testing.T) {
	root := generateInto(t)

	subagents := filepath.Join(root, "claude-dir", "projects", "-x-proj", "sess-0001", "subagents")
	if _, err := os.Stat(filepath.Join(subagents, "agent-B.jsonl")); err != nil {
		t.Fatalf("agent-B.jsonl missing: %v", err)
	}
	if _, err := os.Stat(filepath.Join(subagents, "agent-B.meta.json")); !os.IsNotExist(err) {
		t.Fatalf("agent-B.meta.json must not exist, stat err = %v", err)
	}
	if _, err := os.Stat(filepath.Join(subagents, "agent-A.meta.json")); err != nil {
		t.Fatalf("agent-A.meta.json missing: %v", err)
	}
}

func TestGenerateCreatesNestedWorkflowAgentWithMeta(t *testing.T) {
	root := generateInto(t)

	wfDir := filepath.Join(root, "claude-dir", "projects", "-x-proj", "sess-0001",
		"subagents", "workflows", "wf_test")
	if _, err := os.Stat(filepath.Join(wfDir, "agent-W.jsonl")); err != nil {
		t.Fatalf("nested workflow agent-W.jsonl missing: %v", err)
	}
	meta, err := os.ReadFile(filepath.Join(wfDir, "agent-W.meta.json"))
	if err != nil {
		t.Fatalf("agent-W.meta.json missing: %v", err)
	}
	var m struct {
		AgentType string  `json:"agentType"`
		ToolUseID *string `json:"toolUseId"`
	}
	if err := json.Unmarshal(meta, &m); err != nil {
		t.Fatalf("agent-W.meta.json invalid JSON: %v", err)
	}
	if m.AgentType != "workflow-subagent" {
		t.Errorf("agent-W agentType = %q, want %q", m.AgentType, "workflow-subagent")
	}
	if m.ToolUseID != nil {
		t.Errorf("agent-W.meta.json must carry NO toolUseId (real workflow metas have none; linkage is via the path runId), got %q", *m.ToolUseID)
	}
}

func TestGenerateCreatesWorkflowSpawnedScoutWithToolUseIDMeta(t *testing.T) {
	root := generateInto(t)

	wfDir := filepath.Join(root, "claude-dir", "projects", "-x-proj", "sess-0001",
		"subagents", "workflows", "wf_test")
	if _, err := os.Stat(filepath.Join(wfDir, "agent-WS.jsonl")); err != nil {
		t.Fatalf("agent-WS.jsonl missing: %v", err)
	}
	meta, err := os.ReadFile(filepath.Join(wfDir, "agent-WS.meta.json"))
	if err != nil {
		t.Fatalf("agent-WS.meta.json missing: %v", err)
	}
	var m struct {
		AgentType string `json:"agentType"`
		ToolUseID string `json:"toolUseId"`
	}
	if err := json.Unmarshal(meta, &m); err != nil {
		t.Fatalf("agent-WS.meta.json invalid JSON: %v", err)
	}
	if m.AgentType != "scout" {
		t.Errorf("agent-WS agentType = %q, want %q", m.AgentType, "scout")
	}
	if m.ToolUseID != "toolu_WS" {
		t.Errorf("agent-WS toolUseId = %q, want %q (depth-2 linkage into agent-W)", m.ToolUseID, "toolu_WS")
	}
}

func TestGenerateLinksAgentAToolUseIDToMainTranscriptToolUseBlock(t *testing.T) {
	root := generateInto(t)

	sub := filepath.Join(root, "claude-dir", "projects", "-x-proj", "sess-0001", "subagents")
	meta, err := os.ReadFile(filepath.Join(sub, "agent-A.meta.json"))
	if err != nil {
		t.Fatalf("agent-A.meta.json missing: %v", err)
	}
	var m struct {
		ToolUseID string `json:"toolUseId"`
	}
	if err := json.Unmarshal(meta, &m); err != nil {
		t.Fatalf("agent-A.meta.json invalid JSON: %v", err)
	}
	if m.ToolUseID == "" {
		t.Fatal("agent-A.meta.json must contain a nonempty toolUseId")
	}
	main, err := os.ReadFile(filepath.Join(root, "claude-dir", "projects", "-x-proj", "sess-0001.jsonl"))
	if err != nil {
		t.Fatal(err)
	}
	if !strings.Contains(string(main), `"id":"`+m.ToolUseID+`"`) {
		t.Errorf("main transcript has no tool_use block with id %q", m.ToolUseID)
	}
}

func TestGenerateTruncatesOnlyFinalLineOfMarkedFile(t *testing.T) {
	root := generateInto(t)

	expected := readExpected(t, root)
	rel, ok := expected["truncated_file"].(string)
	if !ok || rel == "" {
		t.Fatal("expected.json must record truncated_file")
	}
	// truncated_file is repo-relative (testdata/claude-dir/...); map into root.
	inRoot := filepath.Join(root, strings.TrimPrefix(rel, "testdata/"))
	data, err := os.ReadFile(inRoot)
	if err != nil {
		t.Fatalf("read truncated file: %v", err)
	}
	lines := strings.Split(strings.TrimRight(string(data), "\n"), "\n")
	if len(lines) < 2 {
		t.Fatalf("truncated file needs >= 2 lines, got %d", len(lines))
	}
	last := lines[len(lines)-1]
	var v any
	if err := json.Unmarshal([]byte(last), &v); err == nil {
		t.Errorf("final line must be truncated JSON, but it parsed: %q", last)
	}
	if err := json.Unmarshal([]byte(lines[len(lines)-2]), &v); err != nil {
		t.Errorf("second-to-last line must be valid JSON: %v", err)
	}
}

func TestGenerateWritesExpectedJSONWithRequiredKeys(t *testing.T) {
	root := generateInto(t)

	expected := readExpected(t, root)
	for _, key := range []string{"sample_count", "total_output_tokens", "total_input_tokens", "per_root_frame", "stacks", "truncated_file"} {
		if _, ok := expected[key]; !ok {
			t.Errorf("expected.json missing key %q", key)
		}
	}
}

func TestGenerateWritesExpectedCostTotals(t *testing.T) {
	root := generateInto(t)

	expected := readExpected(t, root)
	// Hand-computed from the fixture inventory and the task 03 rate table:
	// msg_a1 1838 + msg_a2 3000 + msg_sa1 4500 + msg_sb1 600 + msg_b1 0 +
	// msg_b2 0 + req-fallback 2700 + msg_b3 1500 + msg_w1 10500 +
	// msg_ws1 150 = 24788.
	if got, ok := expected["total_cost_microusd"].(float64); !ok || got != 24788 {
		t.Errorf("total_cost_microusd = %v, want 24788", expected["total_cost_microusd"])
	}
	perRoot, ok := expected["per_root_frame"].(map[string]any)
	if !ok {
		t.Fatal("expected.json missing per_root_frame")
	}
	// agent-W and agent-WS live under sess-0001, so 10500 + 150 belong to proj.
	wantRootCost := map[string]float64{"proj": 20588, "beta": 4200}
	for frame, want := range wantRootCost {
		rf, ok := perRoot[frame].(map[string]any)
		if !ok {
			t.Fatalf("per_root_frame missing %q", frame)
		}
		if got, ok := rf["cost_microusd"].(float64); !ok || got != want {
			t.Errorf("per_root_frame[%q].cost_microusd = %v, want %v", frame, rf["cost_microusd"], want)
		}
	}
}

func TestGenerateWritesVertexLogsFixture(t *testing.T) {
	root := generateInto(t)

	data, err := os.ReadFile(filepath.Join(root, "vertex-logs.json"))
	if err != nil {
		t.Fatalf("vertex-logs.json missing: %v", err)
	}
	var rows []map[string]any
	if err := json.Unmarshal(data, &rows); err != nil {
		t.Fatalf("vertex-logs.json is not a JSON array of rows: %v", err)
	}
	if len(rows) != 5 {
		t.Fatalf("vertex-logs.json has %d rows, want 5", len(rows))
	}
	// R12: at least one full_response as a JSON-encoded string and one as an
	// inline object, and one row missing endpoint.
	var asString, asObject, noEndpoint bool
	for _, r := range rows {
		switch r["full_response"].(type) {
		case string:
			asString = true
		case map[string]any:
			asObject = true
		}
		if _, ok := r["endpoint"]; !ok {
			noEndpoint = true
		}
	}
	if !asString {
		t.Error("no row encodes full_response as a JSON-encoded string")
	}
	if !asObject {
		t.Error("no row encodes full_response as an inline object")
	}
	if !noEndpoint {
		t.Error("no row is missing the endpoint column")
	}
}

func TestGenerateIsDeterministic(t *testing.T) {
	root1 := generateInto(t)
	root2 := generateInto(t)

	if !maps.Equal(listFiles(t, root1), listFiles(t, root2)) {
		t.Error("generated trees differ between runs")
	}
}

func readExpected(t *testing.T, root string) map[string]any {
	t.Helper()
	data, err := os.ReadFile(filepath.Join(root, "claude-dir.expected.json"))
	if err != nil {
		t.Fatalf("read expected.json: %v", err)
	}
	var expected map[string]any
	if err := json.Unmarshal(data, &expected); err != nil {
		t.Fatalf("expected.json invalid JSON: %v", err)
	}
	return expected
}

// listFiles returns relative path -> file content for every file under root.
func listFiles(t *testing.T, root string) map[string]string {
	t.Helper()
	files := map[string]string{}
	err := filepath.WalkDir(root, func(path string, d os.DirEntry, err error) error {
		if err != nil {
			return err
		}
		if d.IsDir() {
			return nil
		}
		data, err := os.ReadFile(path)
		if err != nil {
			return err
		}
		rel, _ := filepath.Rel(root, path)
		files[rel] = string(data)
		return nil
	})
	if err != nil {
		t.Fatal(err)
	}
	return files
}
