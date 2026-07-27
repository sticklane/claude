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

	"github.com/sticklane/agentprof/internal/claude"
)

// commandName matches the tag Claude Code writes into a user turn when the
// turn came from a slash command.
var commandName = regexp.MustCompile(`<command-name>([^<]{1,80})</command-name>`)

type transcriptToolUse struct {
	Type string `json:"type"`
	Name string `json:"name"`
}

type transcriptRecord struct {
	Type      string `json:"type"`
	Timestamp string `json:"timestamp"`
	Message   *struct {
		Content json.RawMessage `json:"content"`
	} `json:"message"`
}

// ReadClaude walks a Claude Code projects directory and returns every skill
// activation and tool call recorded at or after cutoff. Claude Code is the one
// harness that records who chose the skill: a turn carrying a <command-name>
// tag was typed by the user, anything else was the model's own decision.
//
// A typed slash command does not reliably emit a Skill tool call — the command
// often expands straight into the prompt — so command tags are counted as
// activations in their own right, deduplicated against any Skill tool call the
// same turn produced. known filters those tags to installed skills so ordinary
// commands (/clear, /compact) are not miscounted as skills; a nil known
// accepts every tag.
func ReadClaude(dir string, cutoff time.Time, known map[string]bool) ([]Activation, error) {
	var out []Activation
	err := filepath.WalkDir(dir, func(path string, d fs.DirEntry, err error) error {
		if err != nil || d.IsDir() || !strings.HasSuffix(path, ".jsonl") {
			return nil
		}
		info, statErr := d.Info()
		if statErr != nil || info.ModTime().Before(cutoff) {
			return nil
		}
		session := strings.TrimSuffix(filepath.Base(path), ".jsonl")
		project := filepath.Base(filepath.Dir(path))
		skills, matchedTags := claudeSkills(path, session, project)
		out = append(out, skills...)
		out = append(out, claudeTools(path, session, project)...)
		out = append(out, claudeCommands(path, session, project, known, matchedTags)...)
		return nil
	})
	return out, err
}

// claudeSkills returns the Skill tool calls in one transcript, and a count per
// skill name of those whose turn carried a matching command tag — the calls
// claudeCommands must not count a second time.
func claudeSkills(path, session, project string) ([]Activation, map[string]int) {
	invs, err := claude.SkillInvocations(path)
	if err != nil {
		return nil, nil
	}
	out := make([]Activation, 0, len(invs))
	matchedTags := map[string]int{}
	for _, inv := range invs {
		if inv.Name == "" {
			continue
		}
		invocation := InvocationAuto
		if tag := commandSkill(inv.CommandTag); tag != "" && tag == NormalizeName(inv.Name) {
			invocation = InvocationExplicit
			matchedTags[tag]++
		}
		out = append(out, Activation{
			Harness: "claude", Session: session, Project: project,
			Kind: KindSkill, Name: inv.Name, Invocation: invocation,
		})
	}
	return out, matchedTags
}

func claudeCommands(path, session, project string, known map[string]bool, matchedTags map[string]int) []Activation {
	f, err := os.Open(path)
	if err != nil {
		return nil
	}
	defer f.Close()

	var out []Activation
	sc := bufio.NewScanner(f)
	sc.Buffer(make([]byte, 64*1024), maxRolloutLine)
	for sc.Scan() {
		var r transcriptRecord
		if json.Unmarshal(sc.Bytes(), &r) != nil || r.Type != "user" || r.Message == nil {
			continue
		}
		m := commandName.FindSubmatch(r.Message.Content)
		if m == nil {
			continue
		}
		name := commandSkill(string(m[1]))
		if name == "" || (known != nil && !known[name]) {
			continue
		}
		if matchedTags[name] > 0 {
			matchedTags[name]--
			continue
		}
		at, _ := time.Parse(time.RFC3339, r.Timestamp)
		out = append(out, Activation{
			Harness: "claude", Session: session, Project: project,
			Kind: KindSkill, Name: name, Invocation: InvocationExplicit, At: at,
		})
	}
	return out
}

// commandSkill reduces a <command-name> tag to the skill it names: the leading
// slash and any plugin namespace are dropped. It returns "" for a tag that
// cannot name a skill, including the regex placeholder Claude Code writes when
// a command has no name.
func commandSkill(tag string) string {
	name := NormalizeName(strings.TrimPrefix(strings.TrimSpace(tag), "/"))
	if name == "" || strings.ContainsAny(name, "(.*?)<> ") {
		return ""
	}
	return name
}

func claudeTools(path, session, project string) []Activation {
	f, err := os.Open(path)
	if err != nil {
		return nil
	}
	defer f.Close()

	var out []Activation
	sc := bufio.NewScanner(f)
	sc.Buffer(make([]byte, 64*1024), maxRolloutLine)
	for sc.Scan() {
		var r transcriptRecord
		if json.Unmarshal(sc.Bytes(), &r) != nil || r.Type != "assistant" || r.Message == nil {
			continue
		}
		var blocks []transcriptToolUse
		if json.Unmarshal(r.Message.Content, &blocks) != nil {
			continue
		}
		at, _ := time.Parse(time.RFC3339, r.Timestamp)
		for _, b := range blocks {
			if b.Type != "tool_use" || b.Name == "" || b.Name == "Skill" {
				continue
			}
			out = append(out, Activation{
				Harness: "claude", Session: session, Project: project,
				Kind: KindTool, Name: b.Name, Invocation: InvocationUnknown, At: at,
			})
		}
	}
	return out
}
