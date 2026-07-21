package claude_test

import (
	"os"
	"path/filepath"
	"testing"

	"github.com/sticklane/agentprof/internal/claude"
)

// writeTranscript writes the given JSONL lines to a temp .jsonl file and
// returns its path.
func writeTranscript(t *testing.T, lines ...string) string {
	t.Helper()
	dir := t.TempDir()
	path := filepath.Join(dir, "session.jsonl")
	content := ""
	for _, l := range lines {
		content += l + "\n"
	}
	if err := os.WriteFile(path, []byte(content), 0o644); err != nil {
		t.Fatal(err)
	}
	return path
}

// skillInvocationFixture is a transcript with three Skill tool_use invocations:
//   - toolu_1: model-auto-triggered in a plain user turn (no command tag).
//   - toolu_2: a self-chain — a second skill invoked inside an assistant turn
//     with no new preceding user message.
//   - toolu_3: invoked in a turn opened by a <command-name>build</command-name>
//     tag, carrying args.
func skillInvocationFixture() []string {
	return []string{
		`{"type":"user","timestamp":"2026-07-01T09:00:00Z","cwd":"/x/app","message":{"role":"user","content":"start please"}}`,
		`{"type":"assistant","timestamp":"2026-07-01T09:00:01Z","cwd":"/x/app","message":{"id":"m1","model":"claude-fable-5","content":[{"type":"tool_use","id":"toolu_1","name":"Skill","input":{"command":"morning-brief"}}]}}`,
		`{"type":"user","timestamp":"2026-07-01T09:00:02Z","cwd":"/x/app","message":{"role":"user","content":[{"type":"tool_result","tool_use_id":"toolu_1","content":"brief ready"}]}}`,
		`{"type":"assistant","timestamp":"2026-07-01T09:00:03Z","cwd":"/x/app","message":{"id":"m2","model":"claude-fable-5","content":[{"type":"tool_use","id":"toolu_2","name":"Skill","input":{"command":"daily-sync"}}]}}`,
		`{"type":"user","timestamp":"2026-07-01T09:00:04Z","cwd":"/x/app","message":{"role":"user","content":[{"type":"tool_result","tool_use_id":"toolu_2","content":"synced"}]}}`,
		`{"type":"user","timestamp":"2026-07-01T09:00:05Z","cwd":"/x/app","message":{"role":"user","content":"<command-name>build</command-name><command-args>specs/x</command-args>"}}`,
		`{"type":"assistant","timestamp":"2026-07-01T09:00:06Z","cwd":"/x/app","message":{"id":"m3","model":"claude-fable-5","content":[{"type":"tool_use","id":"toolu_3","name":"Skill","input":{"command":"build","args":"specs/x"}}]}}`,
		`{"type":"user","timestamp":"2026-07-01T09:00:07Z","cwd":"/x/app","message":{"role":"user","content":[{"type":"tool_result","tool_use_id":"toolu_3","content":"built"}]}}`,
	}
}

func TestSkillInvocationsPairsResultsCommandTagsAndUserTurns(t *testing.T) {
	path := writeTranscript(t, skillInvocationFixture()...)

	invs, err := claude.SkillInvocations(path)
	if err != nil {
		t.Fatalf("SkillInvocations: %v", err)
	}
	if len(invs) != 3 {
		t.Fatalf("got %d invocations, want 3: %+v", len(invs), invs)
	}

	// Invocation 1: model-auto-triggered, plain user turn.
	if invs[0].Name != "morning-brief" {
		t.Errorf("inv[0].Name = %q, want morning-brief", invs[0].Name)
	}
	if invs[0].Result != "brief ready" {
		t.Errorf("inv[0].Result = %q, want %q", invs[0].Result, "brief ready")
	}
	if invs[0].CommandTag != "" {
		t.Errorf("inv[0].CommandTag = %q, want empty", invs[0].CommandTag)
	}
	if !invs[0].PrecededByUserTurn {
		t.Error("inv[0].PrecededByUserTurn = false, want true (a user turn opened before it)")
	}

	// Invocation 2: self-chain — no new user message intervened.
	if invs[1].Name != "daily-sync" {
		t.Errorf("inv[1].Name = %q, want daily-sync", invs[1].Name)
	}
	if invs[1].Result != "synced" {
		t.Errorf("inv[1].Result = %q, want synced", invs[1].Result)
	}
	if invs[1].PrecededByUserTurn {
		t.Error("inv[1].PrecededByUserTurn = true, want false (self-chain, no intervening user turn)")
	}

	// Invocation 3: opened by a <command-name> tag, with args.
	if invs[2].Name != "build" {
		t.Errorf("inv[2].Name = %q, want build", invs[2].Name)
	}
	if invs[2].Args != "specs/x" {
		t.Errorf("inv[2].Args = %q, want specs/x", invs[2].Args)
	}
	if invs[2].Result != "built" {
		t.Errorf("inv[2].Result = %q, want built", invs[2].Result)
	}
	if invs[2].CommandTag != "build" {
		t.Errorf("inv[2].CommandTag = %q, want build", invs[2].CommandTag)
	}
	if !invs[2].PrecededByUserTurn {
		t.Error("inv[2].PrecededByUserTurn = false, want true")
	}
}
