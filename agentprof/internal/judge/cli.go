package judge

import (
	"context"
	"encoding/json"
	"fmt"
	"os"
	"os/exec"
	"time"
)

const cliTimeout = 120 * time.Second

// CLIJudge grades with one `claude -p <prompt> --model <tier> --output-format
// json` subprocess call per invocation. ScratchRoot is the base under which
// each call gets a fresh CLAUDE_CONFIG_DIR, so grading sessions never pollute
// the profiled ~/.claude tree and never share config state across calls (R12).
type CLIJudge struct {
	ScratchRoot string
}

var _ Judge = (*CLIJudge)(nil)

// Judge runs one grading subprocess and returns the CLI reply's result text.
func (j *CLIJudge) Judge(prompt, tier string) (string, error) {
	ctx, cancel := context.WithTimeout(context.Background(), cliTimeout)
	defer cancel()
	cmd, err := j.command(ctx, prompt, tier)
	if err != nil {
		return "", err
	}
	out, err := cmd.Output()
	if err != nil {
		return "", fmt.Errorf("claude subprocess: %w", err)
	}
	return parseResult(out)
}

// command builds the subprocess with a fresh per-invocation scratch config dir;
// split out (and creating the dir here) so tests can assert its env without a
// real subprocess call (R12).
func (j *CLIJudge) command(ctx context.Context, prompt, tier string) (*exec.Cmd, error) {
	if j.ScratchRoot != "" {
		if err := os.MkdirAll(j.ScratchRoot, 0o755); err != nil {
			return nil, fmt.Errorf("creating scratch root: %w", err)
		}
	}
	dir, err := os.MkdirTemp(j.ScratchRoot, "judge-")
	if err != nil {
		return nil, fmt.Errorf("creating scratch config dir: %w", err)
	}
	cmd := exec.CommandContext(ctx, "claude", "-p", prompt, "--model", tier, "--output-format", "json")
	cmd.Env = append(os.Environ(), "CLAUDE_CONFIG_DIR="+dir)
	return cmd, nil
}

// parseResult extracts the "result" field from the CLI's JSON output.
func parseResult(out []byte) (string, error) {
	var reply struct {
		Result string `json:"result"`
	}
	if err := json.Unmarshal(out, &reply); err != nil {
		return "", fmt.Errorf("subprocess output: %w", err)
	}
	return reply.Result, nil
}
