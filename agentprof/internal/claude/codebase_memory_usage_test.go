package claude_test

import (
	"os"
	"path/filepath"
	"testing"

	"github.com/sticklane/agentprof/internal/claude"
	"github.com/sticklane/agentprof/internal/schema"
)

func codebaseMemorySessionDir(t *testing.T, cwd string) string {
	t.Helper()
	claudeDir := t.TempDir()
	projectDir := filepath.Join(claudeDir, "projects", "-repo")
	if err := os.MkdirAll(projectDir, 0o755); err != nil {
		t.Fatal(err)
	}
	line := `{"type":"assistant","timestamp":"2026-07-01T09:00:00Z","cwd":"` + cwd + `","sessionId":"sess-cbm","message":{"model":"claude-fable-5","usage":{"input_tokens":10,"output_tokens":1},"content":[` +
		`{"type":"tool_use","id":"t1","name":"mcp__codebase-memory-mcp__search_graph","input":{"name_pattern":"Collect"}},` +
		`{"type":"tool_use","id":"t2","name":"Bash","input":{"command":"agentic-codebase-memory-mcp cli get_architecture --project repo"}},` +
		`{"type":"tool_use","id":"t3","name":"Skill","input":{"skill":"agentic:codebase-memory"}},` +
		`{"type":"tool_use","id":"t4","name":"search_code","input":{"query":"generic server"}},` +
		`{"type":"tool_use","id":"t5","name":"Bash","input":{"command":"/opt/agentic/bin/agentic-codebase-memory-mcp cli search_code --query Collect"}},` +
		`{"type":"tool_use","id":"t6","name":"Bash","input":{"command":"grep -rn getExecutionCtx ."}}` +
		`]}}`
	if err := os.WriteFile(
		filepath.Join(projectDir, "sess-cbm.jsonl"),
		[]byte(line+"\n"),
		0o644,
	); err != nil {
		t.Fatal(err)
	}
	return claudeDir
}

func mainLoopCodebaseMemoryUsage(t *testing.T, samples []schema.Sample) int64 {
	t.Helper()
	for _, sample := range samples {
		if _, ok := sample.Values["calls"]; ok {
			return sample.Values["codebase_memory_usage"]
		}
	}
	t.Fatal("no main-loop model-call sample found")
	return 0
}

func TestCollectCountsCodebaseMemoryUsage(t *testing.T) {
	samples, _, _, err := claude.Collect(
		codebaseMemorySessionDir(t, t.TempDir()),
		anyCutoff,
	)
	if err != nil {
		t.Fatalf("Collect: %v", err)
	}
	if got := mainLoopCodebaseMemoryUsage(t, samples); got != 4 {
		t.Errorf("codebase_memory_usage = %d, want 4", got)
	}
}

func TestCollectDoesNotRequireCheckoutGraphState(t *testing.T) {
	repo := t.TempDir()
	samples, _, _, err := claude.Collect(
		codebaseMemorySessionDir(t, repo),
		anyCutoff,
	)
	if err != nil {
		t.Fatalf("Collect: %v", err)
	}
	if got := mainLoopCodebaseMemoryUsage(t, samples); got != 4 {
		t.Errorf("codebase_memory_usage = %d, want 4 without checkout state", got)
	}
}
