package claude_test

import (
	"os"
	"path/filepath"
	"testing"

	"github.com/sticklane/agentprof/internal/claude"
	"github.com/sticklane/agentprof/internal/schema"
)

// ctxSessionDir writes a one-response session whose assistant message issues
// two ctx-verb Bash calls, one agentic:ctx Skill call, and one Bash call where
// "ctx" appears only as an identifier substring (getExecutionCtx). It returns a
// claude-dir to hand to Collect; cwd is the session's recorded working dir,
// which the caller sets up as indexed (.context/ present) or not.
func ctxSessionDir(t *testing.T, cwd string) string {
	t.Helper()
	claudeDir := t.TempDir()
	proj := filepath.Join(claudeDir, "projects", "-repo")
	if err := os.MkdirAll(proj, 0o755); err != nil {
		t.Fatal(err)
	}
	line := `{"type":"assistant","timestamp":"2026-07-01T09:00:00Z","cwd":"` + cwd + `","sessionId":"sess-ctx","message":{"model":"claude-fable-5","usage":{"input_tokens":10,"output_tokens":1},"content":[` +
		`{"type":"tool_use","id":"t1","name":"Bash","input":{"command":"ctx tree internal/claude/claude.go"}},` +
		`{"type":"tool_use","id":"t2","name":"Bash","input":{"command":"cd agentprof && ctx refs Collect"}},` +
		`{"type":"tool_use","id":"t3","name":"Skill","input":{"command":"agentic:ctx"}},` +
		`{"type":"tool_use","id":"t4","name":"Bash","input":{"command":"grep -rn getExecutionCtx ."}}` +
		`]}}`
	if err := os.WriteFile(filepath.Join(proj, "sess-ctx.jsonl"), []byte(line+"\n"), 0o644); err != nil {
		t.Fatal(err)
	}
	return claudeDir
}

// mainLoopCtxUsage returns the ctx_usage value on the session's single
// main-loop model-call sample (the sample carrying a "calls" value).
func mainLoopCtxUsage(t *testing.T, samples []schema.Sample) int64 {
	t.Helper()
	for _, s := range samples {
		if _, ok := s.Values["calls"]; ok {
			return s.Values["ctx_usage"]
		}
	}
	t.Fatal("no main-loop model-call sample found")
	return 0
}

func TestCollectCountsCtxUsageForIndexedRepoSession(t *testing.T) {
	repo := t.TempDir()
	if err := os.Mkdir(filepath.Join(repo, ".context"), 0o755); err != nil {
		t.Fatal(err)
	}
	samples, _, _, err := claude.Collect(ctxSessionDir(t, repo), anyCutoff)
	if err != nil {
		t.Fatalf("Collect: %v", err)
	}
	// 2 ctx-verb Bash calls + 1 agentic:ctx Skill = 3; the getExecutionCtx
	// substring Bash call is not counted.
	if got := mainLoopCtxUsage(t, samples); got != 3 {
		t.Errorf("ctx_usage = %d, want 3 (2 bash + 1 skill; substring excluded)", got)
	}
}

func TestCollectExcludesCtxUsageForNonIndexedRepoSession(t *testing.T) {
	repo := t.TempDir() // no .context/ -> not an indexed repo
	samples, _, _, err := claude.Collect(ctxSessionDir(t, repo), anyCutoff)
	if err != nil {
		t.Fatalf("Collect: %v", err)
	}
	if got := mainLoopCtxUsage(t, samples); got != 0 {
		t.Errorf("ctx_usage = %d, want 0 (cwd is not an indexed repo)", got)
	}
}
