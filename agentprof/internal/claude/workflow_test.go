package claude_test

import (
	"os"
	"path/filepath"
	"strings"
	"testing"

	"github.com/sticklane/agentprof/internal/claude"
)

// Workflow-subagent linkage (workflow-linkage SPEC R1-R5, R7): agents under
// subagents/workflows/<runId>/ whose meta lacks a toolUseId resolve through
// the session's runId -> tool_use_id map recorded from toolUseResult lines,
// and gain a wf:<workflowName> frame before their agent: frame.

// writeAgent writes one subagent transcript (and its meta, unless metaJSON is
// empty) at rel under the sess-z session directory of dir.
func writeAgent(t *testing.T, dir, rel, metaJSON string, lines ...string) {
	t.Helper()
	path := filepath.Join(dir, "projects", "-z-app", "sess-z", rel)
	if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
		t.Fatal(err)
	}
	content := strings.Join(lines, "\n") + "\n"
	if err := os.WriteFile(path, []byte(content), 0o644); err != nil {
		t.Fatal(err)
	}
	if metaJSON == "" {
		return
	}
	metaPath := strings.TrimSuffix(path, ".jsonl") + ".meta.json"
	if err := os.WriteFile(metaPath, []byte(metaJSON+"\n"), 0o644); err != nil {
		t.Fatal(err)
	}
}

func agentAssistantLine(msgID string) string {
	return `{"type":"assistant","timestamp":"2026-07-01T09:20:00Z","cwd":"/z/app","sessionId":"sess-z","message":{"id":"` + msgID + `","model":"claude-haiku-4-5","usage":{"input_tokens":5,"output_tokens":1}}}`
}

// mainWithWorkflowRun is a main transcript: turn 01 ("hi"), an assistant line
// carrying tool_use blocks toolu_ag (Agent) and toolu_wf (Workflow), and the
// Workflow tool_result line recording run wf_x named "flow".
func mainWithWorkflowRun() []string {
	return []string{
		`{"type":"user","timestamp":"2026-07-01T09:00:00Z","cwd":"/z/app","sessionId":"sess-z","message":{"role":"user","content":"hi"}}`,
		`{"type":"assistant","timestamp":"2026-07-01T09:01:00Z","cwd":"/z/app","sessionId":"sess-z","message":{"id":"m1","model":"claude-fable-5","content":[{"type":"tool_use","id":"toolu_ag","name":"Agent"},{"type":"tool_use","id":"toolu_wf","name":"Workflow"}],"usage":{"input_tokens":10,"output_tokens":1}}}`,
		`{"type":"user","timestamp":"2026-07-01T09:02:00Z","cwd":"/z/app","sessionId":"sess-z","message":{"role":"user","content":[{"type":"tool_result","tool_use_id":"toolu_wf","content":"launched"}]},"toolUseResult":{"status":"async_launched","runId":"wf_x","workflowName":"flow"}}`,
	}
}

func TestCollectLinksWorkflowAgentViaPathRunID(t *testing.T) {
	dir := writeMain(t, mainWithWorkflowRun()...)
	writeAgent(t, dir, "subagents/workflows/wf_x/agent-M.jsonl",
		`{"agentType":"workflow-subagent","spawnDepth":1}`,
		agentAssistantLine("m_ag1"))

	samples, _, _, err := claude.Collect(dir, anyCutoff)
	if err != nil {
		t.Fatalf("Collect: %v", err)
	}
	got := findByStack(samples, []string{"app", "t01 · hi", "(no skill)", "main",
		"wf:flow", "agent:workflow-subagent", "claude-haiku-4-5"})
	if len(got) != 1 {
		t.Fatalf("got %d run-linked samples, want 1; all samples: %v", len(got), stacks(samples))
	}
	if turn := got[0].Labels["turn"]; turn != "01" {
		t.Errorf("run-linked sample turn label = %q, want %q (inherited from the spawning tool_use line)", turn, "01")
	}
}

func TestCollectMetaToolUseIDTakesPrecedenceOverPathRunID(t *testing.T) {
	dir := writeMain(t, mainWithWorkflowRun()...)
	// The agent lives in the wf_x run directory, but its meta carries a
	// toolUseId (toolu_ag): it must resolve exactly as today, with no wf: frame.
	writeAgent(t, dir, "subagents/workflows/wf_x/agent-M.jsonl",
		`{"agentId":"agent-M","agentType":"scout","toolUseId":"toolu_ag","spawnDepth":1}`,
		agentAssistantLine("m_ag1"))

	samples, _, _, err := claude.Collect(dir, anyCutoff)
	if err != nil {
		t.Fatalf("Collect: %v", err)
	}
	got := findByStack(samples, []string{"app", "t01 · hi", "(no skill)", "main",
		"agent:scout", "claude-haiku-4-5"})
	if len(got) != 1 {
		t.Fatalf("got %d meta-linked samples, want 1; all samples: %v", len(got), stacks(samples))
	}
}

func TestCollectMarksWorkflowAgentWithUnknownRunIDUnlinked(t *testing.T) {
	dir := writeMain(t, mainWithWorkflowRun()...)
	// wf_missing never appears in a toolUseResult line -> R5 unlinked stack.
	writeAgent(t, dir, "subagents/workflows/wf_missing/agent-M.jsonl",
		`{"agentType":"workflow-subagent","spawnDepth":1}`,
		agentAssistantLine("m_ag1"))

	samples, _, _, err := claude.Collect(dir, anyCutoff)
	if err != nil {
		t.Fatalf("Collect: %v", err)
	}
	got := findByStack(samples, []string{"app", "(unlinked)", "agent:workflow-subagent", "claude-haiku-4-5"})
	if len(got) != 1 {
		t.Fatalf("got %d unlinked samples, want 1; all samples: %v", len(got), stacks(samples))
	}
	if _, ok := got[0].Labels["turn"]; ok {
		t.Errorf("unlinked sample must carry no turn label, got %q", got[0].Labels["turn"])
	}
}

func TestCollectUsesUnknownWorkflowNameWhenRunRecordsNone(t *testing.T) {
	main := mainWithWorkflowRun()
	// Same run line but without a workflowName.
	main[2] = `{"type":"user","timestamp":"2026-07-01T09:02:00Z","cwd":"/z/app","sessionId":"sess-z","message":{"role":"user","content":[{"type":"tool_result","tool_use_id":"toolu_wf","content":"launched"}]},"toolUseResult":{"status":"async_launched","runId":"wf_x"}}`
	dir := writeMain(t, main...)
	writeAgent(t, dir, "subagents/workflows/wf_x/agent-M.jsonl",
		`{"agentType":"workflow-subagent","spawnDepth":1}`,
		agentAssistantLine("m_ag1"))

	samples, _, _, err := claude.Collect(dir, anyCutoff)
	if err != nil {
		t.Fatalf("Collect: %v", err)
	}
	got := findByStack(samples, []string{"app", "t01 · hi", "(no skill)", "main",
		"wf:(unknown)", "agent:workflow-subagent", "claude-haiku-4-5"})
	if len(got) != 1 {
		t.Fatalf("got %d wf:(unknown) samples, want 1; all samples: %v", len(got), stacks(samples))
	}
}

func TestCollectChildOfRunLinkedAgentInheritsSingleWorkflowFrame(t *testing.T) {
	dir := writeMain(t, mainWithWorkflowRun()...)
	// agent-P is run-linked; its transcript spawns agent-C via toolu_c.
	writeAgent(t, dir, "subagents/workflows/wf_x/agent-P.jsonl",
		`{"agentType":"workflow-subagent","spawnDepth":1}`,
		`{"type":"assistant","timestamp":"2026-07-01T09:20:00Z","cwd":"/z/app","sessionId":"sess-z","message":{"id":"m_p1","model":"claude-haiku-4-5","content":[{"type":"tool_use","id":"toolu_c","name":"Agent"}],"usage":{"input_tokens":5,"output_tokens":1}}}`)
	writeAgent(t, dir, "subagents/workflows/wf_x/agent-C.jsonl",
		`{"agentId":"agent-C","agentType":"scout","toolUseId":"toolu_c","spawnDepth":2}`,
		agentAssistantLine("m_c1"))

	samples, _, _, err := claude.Collect(dir, anyCutoff)
	if err != nil {
		t.Fatalf("Collect: %v", err)
	}
	// The child resolves via its meta toolUseId and contributes no wf: frame
	// of its own; exactly one arrives through the parent's prefix (R3).
	got := findByStack(samples, []string{"app", "t01 · hi", "(no skill)", "main",
		"wf:flow", "agent:workflow-subagent", "agent:scout", "claude-haiku-4-5"})
	if len(got) != 1 {
		t.Fatalf("got %d nested-child samples, want 1; all samples: %v", len(got), stacks(samples))
	}
	if turn := got[0].Labels["turn"]; turn != "01" {
		t.Errorf("nested child turn label = %q, want inherited %q", turn, "01")
	}
}

func TestCollectKeepsFirstEntryForDuplicateWorkflowRunID(t *testing.T) {
	main := mainWithWorkflowRun()
	// A second tool_result for the same runId, pointing at a different
	// tool_use and name: the first entry in scan order must win.
	main = append(main,
		`{"type":"assistant","timestamp":"2026-07-01T09:03:00Z","cwd":"/z/app","sessionId":"sess-z","message":{"id":"m2","model":"claude-fable-5","content":[{"type":"tool_use","id":"toolu_wf2","name":"Workflow"}],"usage":{"input_tokens":10,"output_tokens":1}}}`,
		`{"type":"user","timestamp":"2026-07-01T09:04:00Z","cwd":"/z/app","sessionId":"sess-z","message":{"role":"user","content":[{"type":"tool_result","tool_use_id":"toolu_wf2","content":"resumed"}]},"toolUseResult":{"status":"async_launched","runId":"wf_x","workflowName":"second"}}`,
	)
	dir := writeMain(t, main...)
	writeAgent(t, dir, "subagents/workflows/wf_x/agent-M.jsonl",
		`{"agentType":"workflow-subagent","spawnDepth":1}`,
		agentAssistantLine("m_ag1"))

	samples, _, _, err := claude.Collect(dir, anyCutoff)
	if err != nil {
		t.Fatalf("Collect: %v", err)
	}
	got := findByStack(samples, []string{"app", "t01 · hi", "(no skill)", "main",
		"wf:flow", "agent:workflow-subagent", "claude-haiku-4-5"})
	if len(got) != 1 {
		t.Fatalf("got %d wf:flow samples, want 1 (first runId entry wins); all samples: %v", len(got), stacks(samples))
	}
	for _, s := range samples {
		if strings.Contains(strings.Join(s.Stack, " / "), "wf:second") {
			t.Errorf("duplicate runId entry overwrote the first: %v", s.Stack)
		}
	}
}
