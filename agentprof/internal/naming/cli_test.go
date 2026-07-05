package naming

import (
	"context"
	"encoding/json"
	"slices"
	"strings"
	"testing"
)

func jsonString(s string) string {
	b, _ := json.Marshal(s)
	return string(b)
}

func TestCLINamerSubprocessEnvCarriesScratchConfigDir(t *testing.T) {
	n := &CLINamer{ConfigDir: "/scratch/agentprof/claude-config"}
	cmd := n.command(context.Background())

	if !slices.Contains(cmd.Env, "CLAUDE_CONFIG_DIR=/scratch/agentprof/claude-config") {
		t.Errorf("subprocess env lacks scratch CLAUDE_CONFIG_DIR: %v", cmd.Env)
	}
	for i, arg := range cmd.Args {
		if i > 0 && strings.HasPrefix(arg, "CLAUDE_CONFIG_DIR") {
			t.Errorf("config dir passed as argv, must be env: %v", cmd.Args)
		}
	}
	joined := strings.Join(cmd.Args, " ")
	for _, want := range []string{"-p", "--model haiku", "--output-format json"} {
		if !strings.Contains(joined, want) {
			t.Errorf("subprocess args %q lack %q", joined, want)
		}
	}
}

func TestParseReplyStripsOneMarkdownFence(t *testing.T) {
	cases := []struct{ name, result string }{
		{"bare", `{"abc": "fix auth bug"}`},
		{"fenced", "```json\n{\"abc\": \"fix auth bug\"}\n```"},
		{"fenced no lang", "```\n{\"abc\": \"fix auth bug\"}\n```"},
	}
	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			out := `{"result": ` + jsonString(tc.result) + `}`
			names, err := parseReply([]byte(out))
			if err != nil {
				t.Fatalf("parseReply: %v", err)
			}
			if names["abc"] != "fix auth bug" {
				t.Errorf("names = %v", names)
			}
		})
	}
}

func TestParseReplyRejectsBadJSON(t *testing.T) {
	if _, err := parseReply([]byte(`{"result": "not an object"}`)); err == nil {
		t.Error("want error for non-object result")
	}
	if _, err := parseReply([]byte(`garbage`)); err == nil {
		t.Error("want error for non-JSON subprocess output")
	}
}
