package census

import (
	"bufio"
	"encoding/json"
	"io/fs"
	"os"
	"path/filepath"
	"regexp"
	"strings"
	"time"
)

// maxRolloutLine bounds one JSONL record; Codex embeds whole file reads in a
// tool result, so the scanner needs far more than bufio's default.
const maxRolloutLine = 16 * 1024 * 1024

// skillPath matches a SKILL.md under any harness's skills directory. The
// catalog Codex injects into the system prompt lists these same paths, so
// matching is only ever applied to tool-call payloads, never to messages.
var skillPath = regexp.MustCompile(`skills/([a-zA-Z0-9_.-]+)/SKILL\.md`)

// patchMarkers are the shapes a Codex file mutation takes. A tool call
// carrying one is editing the skill rather than following it.
var patchMarkers = []string{"apply_patch", "*** Update File", "*** Add File", "sed -i", "tee "}

type rolloutLine struct {
	Timestamp string `json:"timestamp"`
	Type      string `json:"type"`
	Payload   struct {
		Type      string          `json:"type"`
		ID        string          `json:"id"`
		Cwd       string          `json:"cwd"`
		Name      string          `json:"name"`
		Input     json.RawMessage `json:"input"`
		Arguments json.RawMessage `json:"arguments"`
	} `json:"payload"`
}

// ReadCodex walks a Codex sessions directory and returns every skill
// activation and tool call recorded at or after cutoff. A skill counts as
// activated when a tool call reads its SKILL.md — the mechanic Codex's own
// system prompt mandates ("read its SKILL.md completely before taking task
// actions") — which is why the catalog listing in the prompt is not evidence
// of use and message payloads are never scanned.
func ReadCodex(dir string, cutoff time.Time) ([]Activation, error) {
	var out []Activation
	err := filepath.WalkDir(dir, func(path string, d fs.DirEntry, err error) error {
		if err != nil || d.IsDir() || !strings.HasSuffix(path, ".jsonl") {
			return nil
		}
		acts, readErr := readCodexRollout(path, cutoff)
		if readErr == nil {
			out = append(out, acts...)
		}
		return nil
	})
	return out, err
}

func readCodexRollout(path string, cutoff time.Time) ([]Activation, error) {
	f, err := os.Open(path)
	if err != nil {
		return nil, err
	}
	defer f.Close()

	var (
		out     []Activation
		session string
		project string
	)
	sc := bufio.NewScanner(f)
	sc.Buffer(make([]byte, 64*1024), maxRolloutLine)
	for sc.Scan() {
		var l rolloutLine
		if json.Unmarshal(sc.Bytes(), &l) != nil {
			continue
		}
		at, _ := time.Parse(time.RFC3339, l.Timestamp)
		if l.Type == "session_meta" {
			session = l.Payload.ID
			project = filepath.Base(l.Payload.Cwd)
			if !at.IsZero() && at.Before(cutoff) {
				return nil, nil
			}
			continue
		}
		if l.Payload.Type != "custom_tool_call" && l.Payload.Type != "function_call" {
			continue
		}
		args := string(l.Payload.Input) + string(l.Payload.Arguments)
		base := Activation{
			Harness: "codex", Session: session, Project: project,
			Invocation: InvocationUnknown, At: at,
		}
		if l.Payload.Name != "" {
			tool := base
			tool.Kind = KindTool
			tool.Name = l.Payload.Name
			out = append(out, tool)
		}
		for _, m := range skillPath.FindAllStringSubmatch(args, -1) {
			skill := base
			skill.Kind = KindSkill
			skill.Name = m[1]
			skill.Authoring = mutates(args)
			out = append(out, skill)
		}
	}
	return out, sc.Err()
}

func mutates(args string) bool {
	for _, m := range patchMarkers {
		if strings.Contains(args, m) {
			return true
		}
	}
	return false
}
