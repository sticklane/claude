package naming

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"os"
	"os/exec"
	"strings"
	"time"
)

// namePrompt instructs the CLI model; the candidates arrive on stdin as a
// JSON array of {id, prompt, reply_head} (never argv — batches can exceed
// ARG_MAX, R4).
const namePrompt = `You will receive a JSON array of coding-assistant conversation turns, each {"id", "prompt", "reply_head"}. For each turn, write a short name (2-6 words, lowercase, only letters, digits, spaces, and /._-) describing what the turn did. Respond with ONLY a JSON object mapping every id to its name, no other text.`

const cliTimeout = 120 * time.Second

// CLINamer names turns with one `claude -p --model haiku` subprocess call per
// run (R4). ConfigDir is exported as CLAUDE_CONFIG_DIR so naming sessions
// never pollute the profiled ~/.claude tree.
type CLINamer struct {
	ConfigDir string
}

func (n *CLINamer) Name(cands []Candidate) (map[string]string, error) {
	payload, err := json.Marshal(cands)
	if err != nil {
		return nil, err
	}
	if err := os.MkdirAll(n.ConfigDir, 0o755); err != nil {
		return nil, fmt.Errorf("creating scratch config dir: %w", err)
	}
	ctx, cancel := context.WithTimeout(context.Background(), cliTimeout)
	defer cancel()
	cmd := n.command(ctx)
	cmd.Stdin = bytes.NewReader(payload)
	out, err := cmd.Output()
	if err != nil {
		return nil, fmt.Errorf("claude subprocess: %w", err)
	}
	return parseReply(out)
}

// command builds the subprocess; split out so tests can assert its env (R4).
func (n *CLINamer) command(ctx context.Context) *exec.Cmd {
	cmd := exec.CommandContext(ctx, "claude", "-p", namePrompt, "--model", "haiku", "--output-format", "json")
	cmd.Env = append(os.Environ(), "CLAUDE_CONFIG_DIR="+n.ConfigDir)
	return cmd
}

// parseReply extracts the id->name object from the CLI's JSON output: the
// reply's "result" field, with one surrounding markdown code fence stripped
// if present.
func parseReply(out []byte) (map[string]string, error) {
	var reply struct {
		Result string `json:"result"`
	}
	if err := json.Unmarshal(out, &reply); err != nil {
		return nil, fmt.Errorf("subprocess output: %w", err)
	}
	result := strings.TrimSpace(reply.Result)
	if strings.HasPrefix(result, "```") {
		if _, rest, found := strings.Cut(result, "\n"); found {
			result = strings.TrimSuffix(strings.TrimSpace(rest), "```")
		}
	}
	var names map[string]string
	if err := json.Unmarshal([]byte(result), &names); err != nil {
		return nil, fmt.Errorf("result field: %w", err)
	}
	return names, nil
}
