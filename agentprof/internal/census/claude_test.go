package census

import (
	"os"
	"path/filepath"
	"testing"
	"time"
)

const claudeTranscript = `{"type":"user","message":{"role":"user","content":"<command-message>critique</command-message><command-name>critique</command-name>"}}
{"type":"assistant","message":{"role":"assistant","content":[{"type":"tool_use","id":"t1","name":"Skill","input":{"skill":"agentic:critique"}}]}}
{"type":"user","message":{"role":"user","content":"the spec needs a hard look before I build it"}}
{"type":"assistant","message":{"role":"assistant","content":[{"type":"tool_use","id":"t2","name":"Skill","input":{"skill":"breakdown"}}]}}
{"type":"assistant","message":{"role":"assistant","content":[{"type":"tool_use","id":"t3","name":"Read","input":{"file_path":"/tmp/x"}}]}}
{"type":"assistant","message":{"role":"assistant","content":[{"type":"tool_use","id":"t4","name":"mcp__hub__ynab_budget_summary","input":{}}]}}
`

func writeTranscript(t *testing.T, body string) string {
	t.Helper()
	dir := t.TempDir()
	proj := filepath.Join(dir, "-Users-x-proj")
	if err := os.MkdirAll(proj, 0o755); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(filepath.Join(proj, "sess-9.jsonl"), []byte(body), 0o644); err != nil {
		t.Fatal(err)
	}
	return dir
}

func TestReadClaudeMarksSlashCommandInvocationExplicit(t *testing.T) {
	acts, err := ReadClaude(writeTranscript(t, claudeTranscript), time.Time{}, nil)
	if err != nil {
		t.Fatal(err)
	}
	got := find(t, acts, KindSkill, "agentic:critique")
	if got.Invocation != InvocationExplicit {
		t.Errorf("Invocation = %q, want %q", got.Invocation, InvocationExplicit)
	}
	if got.Session != "sess-9" {
		t.Errorf("Session = %q, want sess-9", got.Session)
	}
}

const slashCommandTranscript = `{"type":"user","message":{"role":"user","content":"<command-name>/breakdown</command-name>"}}
{"type":"assistant","message":{"role":"assistant","content":[{"type":"tool_use","id":"t1","name":"Skill","input":{"skill":"breakdown"}}]}}
{"type":"user","message":{"role":"user","content":"<command-name>/agentic:drain</command-name>"}}
{"type":"assistant","message":{"role":"assistant","content":[{"type":"tool_use","id":"t2","name":"Skill","input":{"skill":"agentic:drain"}}]}}
`

func TestReadClaudeTreatsSlashPrefixedCommandTagAsExplicit(t *testing.T) {
	acts, err := ReadClaude(writeTranscript(t, slashCommandTranscript), time.Time{}, nil)
	if err != nil {
		t.Fatal(err)
	}
	for _, name := range []string{"breakdown", "agentic:drain"} {
		if got := find(t, acts, KindSkill, name).Invocation; got != InvocationExplicit {
			t.Errorf("%s Invocation = %q, want %q — the tag is written /%s", name, got, InvocationExplicit, name)
		}
	}
}

const bareSlashCommandTranscript = `{"type":"user","message":{"role":"user","content":"<command-name>/drain</command-name><command-args>specs/x</command-args>"}}
{"type":"assistant","message":{"role":"assistant","content":[{"type":"tool_use","id":"t1","name":"Bash","input":{}}]}}
{"type":"user","message":{"role":"user","content":"<command-name>/clear</command-name>"}}
`

func TestReadClaudeCountsASlashCommandThatEmitsNoSkillToolCall(t *testing.T) {
	acts, err := ReadClaude(writeTranscript(t, bareSlashCommandTranscript), time.Time{}, map[string]bool{"drain": true})
	if err != nil {
		t.Fatal(err)
	}
	got := find(t, acts, KindSkill, "drain")
	if got.Invocation != InvocationExplicit {
		t.Errorf("Invocation = %q, want %q", got.Invocation, InvocationExplicit)
	}
}

func TestReadClaudeIgnoresCommandTagsThatNameNoInstalledSkill(t *testing.T) {
	acts, err := ReadClaude(writeTranscript(t, bareSlashCommandTranscript), time.Time{}, map[string]bool{"drain": true})
	if err != nil {
		t.Fatal(err)
	}
	for _, a := range acts {
		if a.Kind == KindSkill && a.Name == "clear" {
			t.Fatal("/clear counted as a skill activation")
		}
	}
}

func TestReadClaudeCountsSlashCommandAndItsSkillToolCallOnce(t *testing.T) {
	acts, err := ReadClaude(writeTranscript(t, slashCommandTranscript), time.Time{},
		map[string]bool{"breakdown": true, "drain": true})
	if err != nil {
		t.Fatal(err)
	}
	n := 0
	for _, a := range acts {
		if a.Kind == KindSkill && NormalizeName(a.Name) == "breakdown" {
			n++
		}
	}
	if n != 1 {
		t.Errorf("breakdown activations = %d, want 1 — the tag and its Skill tool call are one invocation", n)
	}
}

func TestReadClaudeMarksModelChosenInvocationAuto(t *testing.T) {
	acts, err := ReadClaude(writeTranscript(t, claudeTranscript), time.Time{}, nil)
	if err != nil {
		t.Fatal(err)
	}
	if got := find(t, acts, KindSkill, "breakdown").Invocation; got != InvocationAuto {
		t.Errorf("Invocation = %q, want %q", got, InvocationAuto)
	}
}

func TestReadClaudeCountsToolsIncludingMCP(t *testing.T) {
	acts, err := ReadClaude(writeTranscript(t, claudeTranscript), time.Time{}, nil)
	if err != nil {
		t.Fatal(err)
	}
	find(t, acts, KindTool, "Read")
	find(t, acts, KindTool, "mcp__hub__ynab_budget_summary")
}

func TestReadClaudeDoesNotCountTheSkillToolAsATool(t *testing.T) {
	acts, err := ReadClaude(writeTranscript(t, claudeTranscript), time.Time{}, nil)
	if err != nil {
		t.Fatal(err)
	}
	for _, a := range acts {
		if a.Kind == KindTool && a.Name == "Skill" {
			t.Fatal("Skill counted as a tool as well as a skill activation")
		}
	}
}

func TestReadClaudeRecordsTheProjectDirectory(t *testing.T) {
	acts, err := ReadClaude(writeTranscript(t, claudeTranscript), time.Time{}, nil)
	if err != nil {
		t.Fatal(err)
	}
	if got := find(t, acts, KindSkill, "breakdown").Project; got != "-Users-x-proj" {
		t.Errorf("Project = %q, want %q", got, "-Users-x-proj")
	}
}
