package census

import (
	"os"
	"path/filepath"
	"testing"
	"time"
)

const codexRollout = `{"timestamp":"2026-07-20T10:00:00.000Z","type":"session_meta","payload":{"id":"sess-1","cwd":"/Users/x/proj"}}
{"timestamp":"2026-07-20T10:00:01.000Z","type":"response_item","payload":{"type":"message","role":"user","content":[{"type":"input_text","text":"### Available skills\ncritique — /Users/x/.agents/skills/critique/SKILL.md\ngate — /Users/x/.agents/skills/gate/SKILL.md"}]}}
{"timestamp":"2026-07-20T10:00:02.000Z","type":"response_item","payload":{"type":"custom_tool_call","name":"exec","input":"const r = await tools.exec_command({\"cmd\":\"sed -n '1,200p' /Users/x/.agents/skills/critique/SKILL.md\"})"}}
{"timestamp":"2026-07-20T10:00:03.000Z","type":"response_item","payload":{"type":"function_call","name":"list_agents","arguments":"{}"}}
{"timestamp":"2026-07-20T10:00:04.000Z","type":"response_item","payload":{"type":"custom_tool_call","name":"exec","input":"const r = await tools.exec_command({\"cmd\":\"apply_patch '*** Update File: /Users/x/.agents/skills/gate/SKILL.md'\"})"}}
`

func writeRollout(t *testing.T, body string) string {
	t.Helper()
	dir := t.TempDir()
	sub := filepath.Join(dir, "2026", "07", "20")
	if err := os.MkdirAll(sub, 0o755); err != nil {
		t.Fatal(err)
	}
	path := filepath.Join(sub, "rollout-2026-07-20T10-00-00-sess-1.jsonl")
	if err := os.WriteFile(path, []byte(body), 0o644); err != nil {
		t.Fatal(err)
	}
	return dir
}

func find(t *testing.T, acts []Activation, kind Kind, name string) Activation {
	t.Helper()
	for _, a := range acts {
		if a.Kind == kind && a.Name == name {
			return a
		}
	}
	t.Fatalf("no %s activation named %q in %+v", kind, name, acts)
	return Activation{}
}

func TestReadCodexCountsSkillReadAsActivation(t *testing.T) {
	acts, err := ReadCodex(writeRollout(t, codexRollout), time.Time{})
	if err != nil {
		t.Fatal(err)
	}
	got := find(t, acts, KindSkill, "critique")
	if got.Harness != "codex" {
		t.Errorf("Harness = %q, want codex", got.Harness)
	}
	if got.Session != "sess-1" {
		t.Errorf("Session = %q, want sess-1", got.Session)
	}
	if got.Project != "proj" {
		t.Errorf("Project = %q, want proj", got.Project)
	}
	if got.Authoring {
		t.Error("Authoring = true, want false for a read")
	}
}

func TestReadCodexIgnoresTheSkillCatalogInThePrompt(t *testing.T) {
	acts, err := ReadCodex(writeRollout(t, codexRollout), time.Time{})
	if err != nil {
		t.Fatal(err)
	}
	for _, a := range acts {
		if a.Kind == KindSkill && a.Name == "gate" && !a.Authoring {
			t.Fatal("catalog listing counted as a gate activation")
		}
	}
	skills := 0
	for _, a := range acts {
		if a.Kind == KindSkill && !a.Authoring {
			skills++
		}
	}
	if skills != 1 {
		t.Errorf("skill activations = %d, want 1 (only the one that was read)", skills)
	}
}

func TestReadCodexMarksAPatchOfSkillSourceAsAuthoring(t *testing.T) {
	acts, err := ReadCodex(writeRollout(t, codexRollout), time.Time{})
	if err != nil {
		t.Fatal(err)
	}
	if !find(t, acts, KindSkill, "gate").Authoring {
		t.Error("Authoring = false, want true for a patch of SKILL.md")
	}
}

func TestReadCodexCountsToolCalls(t *testing.T) {
	acts, err := ReadCodex(writeRollout(t, codexRollout), time.Time{})
	if err != nil {
		t.Fatal(err)
	}
	if find(t, acts, KindTool, "list_agents").Session != "sess-1" {
		t.Error("tool activation lost its session")
	}
	if find(t, acts, KindTool, "exec").Harness != "codex" {
		t.Error("exec tool call not recorded")
	}
}

func TestReadCodexSkipsSessionsBeforeTheCutoff(t *testing.T) {
	acts, err := ReadCodex(writeRollout(t, codexRollout), time.Date(2026, 7, 25, 0, 0, 0, 0, time.UTC))
	if err != nil {
		t.Fatal(err)
	}
	if len(acts) != 0 {
		t.Errorf("got %d activations, want 0 before cutoff", len(acts))
	}
}

func TestReadCodexLeavesInvocationUnknown(t *testing.T) {
	acts, err := ReadCodex(writeRollout(t, codexRollout), time.Time{})
	if err != nil {
		t.Fatal(err)
	}
	if got := find(t, acts, KindSkill, "critique").Invocation; got != InvocationUnknown {
		t.Errorf("Invocation = %q, want %q — Codex records no slash-command marker", got, InvocationUnknown)
	}
}
