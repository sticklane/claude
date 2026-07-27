package main

import (
	"bytes"
	"encoding/json"
	"os"
	"path/filepath"
	"strings"
	"testing"

	"github.com/sticklane/agentprof/internal/census"
)

const censusTranscript = `{"type":"user","message":{"role":"user","content":"<command-name>drain</command-name>"}}
{"type":"assistant","message":{"role":"assistant","content":[{"type":"tool_use","id":"t1","name":"Skill","input":{"skill":"agentic:drain"}}]}}
{"type":"user","message":{"role":"user","content":"take a hard look at this spec"}}
{"type":"assistant","message":{"role":"assistant","content":[{"type":"tool_use","id":"t2","name":"Skill","input":{"skill":"critique"}}]}}
{"type":"assistant","message":{"role":"assistant","content":[{"type":"tool_use","id":"t3","name":"Bash","input":{}}]}}
`

func censusDirs(t *testing.T) (claudeDir, skillsDir string) {
	t.Helper()
	root := t.TempDir()
	claudeDir = filepath.Join(root, "projects")
	proj := filepath.Join(claudeDir, "-Users-x-proj")
	if err := os.MkdirAll(proj, 0o755); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(filepath.Join(proj, "s1.jsonl"), []byte(censusTranscript), 0o644); err != nil {
		t.Fatal(err)
	}
	skillsDir = filepath.Join(root, "skills")
	for _, name := range []string{"drain", "critique", "humanizer"} {
		if err := os.MkdirAll(filepath.Join(skillsDir, name), 0o755); err != nil {
			t.Fatal(err)
		}
		if err := os.WriteFile(filepath.Join(skillsDir, name, "SKILL.md"), []byte("---\nname: "+name+"\n---\n"), 0o644); err != nil {
			t.Fatal(err)
		}
	}
	return claudeDir, skillsDir
}

func runCensus(t *testing.T, extra ...string) (string, int) {
	t.Helper()
	claudeDir, skillsDir := censusDirs(t)
	args := append([]string{
		"--claude-dir", claudeDir,
		"--skills-dir", skillsDir,
		"--codex-dir", filepath.Join(t.TempDir(), "absent"),
		"--antigravity-dir", filepath.Join(t.TempDir(), "absent"),
	}, extra...)
	var out, errBuf bytes.Buffer
	code := cmdCensus(args, &out, &errBuf)
	return out.String(), code
}

func TestCensusJSONReportsPerSkillTotals(t *testing.T) {
	out, code := runCensus(t, "--format", "json")
	if code != 0 {
		t.Fatalf("exit = %d, want 0", code)
	}
	var got struct {
		Skills []struct {
			Name     string         `json:"name"`
			Total    int            `json:"total"`
			Auto     int            `json:"auto"`
			Explicit int            `json:"explicit"`
			By       map[string]int `json:"by_harness"`
		} `json:"skills"`
		Unused []string `json:"unused"`
	}
	if err := json.Unmarshal([]byte(out), &got); err != nil {
		t.Fatalf("output is not JSON: %v", err)
	}
	byName := map[string]int{}
	for _, s := range got.Skills {
		byName[s.Name] = s.Total
	}
	if byName["drain"] != 1 || byName["critique"] != 1 {
		t.Errorf("skill totals = %v, want drain:1 critique:1", byName)
	}
}

func TestCensusJSONReportsInstalledSkillsWithNoUse(t *testing.T) {
	out, _ := runCensus(t, "--format", "json")
	var got struct {
		Unused []string `json:"unused"`
	}
	if err := json.Unmarshal([]byte(out), &got); err != nil {
		t.Fatal(err)
	}
	if len(got.Unused) != 1 || got.Unused[0] != "humanizer" {
		t.Errorf("Unused = %v, want [humanizer]", got.Unused)
	}
}

func TestCensusSeparatesAutoFromExplicitInvocation(t *testing.T) {
	out, _ := runCensus(t, "--format", "json")
	var got struct {
		Skills []struct {
			Name     string `json:"name"`
			Auto     int    `json:"auto"`
			Explicit int    `json:"explicit"`
		} `json:"skills"`
	}
	if err := json.Unmarshal([]byte(out), &got); err != nil {
		t.Fatal(err)
	}
	for _, s := range got.Skills {
		if s.Name == "drain" && s.Explicit != 1 {
			t.Errorf("drain Explicit = %d, want 1", s.Explicit)
		}
		if s.Name == "critique" && s.Auto != 1 {
			t.Errorf("critique Auto = %d, want 1", s.Auto)
		}
	}
}

func TestCensusTableNamesEverySkillItCounted(t *testing.T) {
	out, code := runCensus(t)
	if code != 0 {
		t.Fatalf("exit = %d, want 0", code)
	}
	for _, want := range []string{"drain", "critique", "humanizer"} {
		if !strings.Contains(out, want) {
			t.Errorf("table output omits %q", want)
		}
	}
}

func TestCensusIncludesToolsWhenAsked(t *testing.T) {
	out, _ := runCensus(t, "--format", "json", "--kind", "all")
	var got struct {
		Tools []struct {
			Name string `json:"name"`
		} `json:"tools"`
	}
	if err := json.Unmarshal([]byte(out), &got); err != nil {
		t.Fatal(err)
	}
	if len(got.Tools) == 0 || got.Tools[0].Name != "Bash" {
		t.Errorf("Tools = %+v, want Bash counted", got.Tools)
	}
}

func TestCensusOmitsToolsByDefault(t *testing.T) {
	out, _ := runCensus(t, "--format", "json")
	var got struct {
		Tools []struct {
			Name string `json:"name"`
		} `json:"tools"`
	}
	if err := json.Unmarshal([]byte(out), &got); err != nil {
		t.Fatal(err)
	}
	if len(got.Tools) != 0 {
		t.Errorf("Tools = %+v, want none without --kind all", got.Tools)
	}
}

func TestCensusRejectsDaysWithSince(t *testing.T) {
	_, code := runCensus(t, "--days", "7", "--since", "2026-07-01T00:00:00Z")
	if code == 0 {
		t.Error("exit = 0, want non-zero for mutually exclusive window flags")
	}
}

func TestFilterKindDropsNamesWithNoUse(t *testing.T) {
	stats := []census.Stat{
		{Name: "used", Kind: census.KindSkill, Total: 3},
		{Name: "edited-only", Kind: census.KindSkill, Total: 0, Authoring: 9},
	}
	got := filterKind(stats, census.KindSkill)
	if len(got) != 1 || got[0].Name != "used" {
		t.Errorf("filterKind = %+v, want only the used skill", got)
	}
}
