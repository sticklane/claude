package main

import (
	"flag"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"time"

	"github.com/sticklane/agentprof/internal/claude"
	"github.com/sticklane/agentprof/internal/naming"
	"github.com/sticklane/agentprof/internal/output"
	"github.com/sticklane/agentprof/internal/schema"
)

// cmdClaude emits canonical samples from Claude Code transcripts (R4-R8).
func cmdClaude(args []string, stdout, stderr io.Writer) int {
	fs := flag.NewFlagSet("claude", flag.ContinueOnError)
	fs.SetOutput(stderr)
	dir := fs.String("claude-dir", defaultClaudeDir(), "Claude Code data directory")
	days := fs.Int("days", 30, "include sessions active within the last N days")
	nameTurns := fs.Bool("name-turns", false, "rename uninformative turn frames via one cached haiku call")
	out := fs.String("o", "", "output path: .pb.gz writes a pprof profile, anything else JSONL (default stdout)")
	if err := fs.Parse(args); err != nil {
		return 2
	}

	cutoff := time.Now().AddDate(0, 0, -*days)
	samples, turns, skipped, err := claude.Collect(*dir, cutoff)
	if err != nil {
		fmt.Fprintf(stderr, "agentprof claude: %v\n", err)
		return 1
	}
	if skipped > 0 {
		fmt.Fprintf(stderr, "skipped %d unparseable lines\n", skipped)
	}
	if len(samples) == 0 {
		fmt.Fprintln(stderr, "agentprof claude: no samples found (check --claude-dir and --days)")
		return 1
	}
	if *nameTurns {
		nameTurnFrames(samples, turns, stderr)
	}
	if err := output.Write(samples, *out, stdout); err != nil {
		fmt.Fprintf(stderr, "agentprof claude: %v\n", err)
		return 1
	}
	return 0
}

// nameTurnFrames renames candidate turns' frames to "tNN · <name>" in place,
// keyed by (session, ordinal); unresolved turns keep their snippet frames
// (frame-naming SPEC R3).
func nameTurnFrames(samples []schema.Sample, turns []claude.Turn, stderr io.Writer) {
	var cands []naming.Candidate
	for _, t := range turns {
		if t.Candidate {
			cands = append(cands, naming.Candidate{ID: naming.Key(t.Prompt, t.ReplyHead), Prompt: t.Prompt, ReplyHead: t.ReplyHead})
		}
	}
	if len(cands) == 0 {
		return
	}
	namer := &naming.CLINamer{ConfigDir: naming.ConfigDir()}
	names := naming.Resolve(cands, namer, naming.CachePath(), stderr)

	renames := map[string]map[string]string{} // session -> old frame -> new frame
	for _, t := range turns {
		if !t.Candidate {
			continue
		}
		name, ok := names[naming.Key(t.Prompt, t.ReplyHead)]
		if !ok {
			continue
		}
		if renames[t.Session] == nil {
			renames[t.Session] = map[string]string{}
		}
		renames[t.Session][t.Frame] = fmt.Sprintf("t%02d · %s", t.Ordinal, name)
	}
	for session, m := range renames {
		naming.RewriteFrames(samples, session, m)
	}
}

// defaultClaudeDir is $HOME/.claude, or the bare relative path if the home
// directory cannot be determined.
func defaultClaudeDir() string {
	home, err := os.UserHomeDir()
	if err != nil {
		return ".claude"
	}
	return filepath.Join(home, ".claude")
}
